import { test, expect } from '@playwright/test'
import { randomBytes } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../..')
const assets = path.join(root, 'docs/assets')
const policyFile = path.join(here, 'fixtures/synthetic_browser_policy.txt')
const baseURL = process.env.ATLAS_E2E_BASE_URL || 'http://127.0.0.1:8088'

function promoteSyntheticUser(email) {
  const code = `
import sys
from sqlalchemy import text
from app.database.connection import engine
with engine.begin() as connection:
    if connection.scalar(text("SELECT current_database()")) != "atlas_compose_db":
        raise RuntimeError("Refusing to change a non-Compose database")
    result = connection.execute(
        text("UPDATE users SET role = :role WHERE email = :email AND role = :prior"),
        {"role": "admin", "email": sys.argv[1], "prior": "employee"},
    )
    if result.rowcount != 1:
        raise RuntimeError("Synthetic account promotion did not affect exactly one row")
`
  execFileSync('docker', [
    'compose', '--env-file', '.env.compose', 'exec', '-T', 'backend',
    'python', '-c', code, email,
  ], { cwd: root, stdio: 'pipe' })
}

function assertComposeHealthy() {
  const output = execFileSync('docker', [
    'compose', '--env-file', '.env.compose', 'ps', '--format', 'json',
  ], { cwd: root, encoding: 'utf8' })
  const rows = output.trim().split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line))
  for (const service of ['db', 'backend', 'frontend']) {
    const row = rows.find(item => item.Service === service)
    expect(row, `${service} must be running`).toBeTruthy()
    expect(row.Health, `${service} must be healthy`).toBe('healthy')
  }
}

function parseSseFrames(body) {
  return body.split(/\r?\n\r?\n/).map(frame => {
    const event = frame.match(/^event:\s*(.+)$/m)?.[1]
    const data = frame.match(/^data:\s*(.+)$/m)?.[1]
    return event && data ? { event, data: JSON.parse(data) } : null
  }).filter(Boolean)
}

async function assertViewport(page, width, height) {
  await expect.poll(() => page.evaluate(() => ({
    width: window.innerWidth,
    height: window.innerHeight,
    scrollWidth: document.documentElement.scrollWidth,
  }))).toEqual({ width, height, scrollWidth: width })
}

test('real browser upload, Qwen3 stream, evidence, history, mobile and logout', async ({ page, request }) => {
  mkdirSync(assets, { recursive: true })
  assertComposeHealthy()
  for (const endpoint of ['live', 'ready', 'ollama']) {
    const response = await request.get(`/api/health/${endpoint}`)
    expect(response.status(), `${endpoint} health`).toBe(200)
  }

  const id = randomBytes(4).toString('hex').toUpperCase()
  const email = `atlas-browser-${id.toLowerCase()}@example.com`
  const password = randomBytes(24).toString('base64url')
  const title = `ATLAS Synthetic IT Support Policy ${id}`
  const department = `Synthetic Browser Demo ${id}`
  const question = 'In English, describe the full process for a broken company laptop: the ticket, asset tag, acknowledgement time, replacement approval, and personal-device rule. Cite the policy.'

  const registration = await request.post('/api/users/register', { data: { email, password } })
  expect(registration.status()).toBe(201)
  promoteSyntheticUser(email)

  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto(baseURL)
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('main', { name: 'Policy assistant' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()

  await page.getByRole('button', { name: 'Upload document' }).click()
  await page.getByLabel('Title', { exact: true }).fill(title)
  await page.getByLabel('Department', { exact: true }).fill(department)
  const chooserPromise = page.waitForEvent('filechooser')
  await page.getByLabel('File', { exact: true }).click()
  const chooser = await chooserPromise
  await chooser.setFiles(policyFile)
  await expect(page.getByLabel('File', { exact: true })).toHaveValue(/synthetic_browser_policy\.txt$/)

  const uploadResponsePromise = page.waitForResponse(response =>
    response.url() === `${baseURL}/api/documents/upload` && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Upload', exact: true }).click()
  const uploadResponse = await uploadResponsePromise
  expect(uploadResponse.status()).toBe(201)
  const uploaded = await uploadResponse.json()
  expect(uploaded.processing_status).toBe('processed')
  expect(uploaded.id).toBeGreaterThan(0)

  const library = page.getByRole('complementary', { name: 'Workspace navigation' })
  await expect(library.getByRole('button', { name: title, exact: false })).toBeVisible()
  await library.getByRole('button', { name: department, exact: true }).click()
  await expect(library.locator('.workspace-document-button')).toHaveCount(1)
  await library.getByRole('button', { name: title, exact: false }).click()
  await expect(page.locator('.workspace-chat-header-context')).toContainText(title)
  await assertViewport(page, 1920, 1080)
  await page.screenshot({ path: path.join(assets, 'desktop-workspace-1920x1080.png') })

  await page.setViewportSize({ width: 1440, height: 900 })
  await assertViewport(page, 1440, 900)
  await page.screenshot({ path: path.join(assets, 'desktop-workspace-1440x900.png') })
  await library.getByRole('button', { name: 'Upload document' }).click()
  await page.getByLabel('Title', { exact: true }).fill('ATLAS Synthetic Upload Preview')
  await page.getByLabel('Department', { exact: true }).fill(department)
  const previewChooserPromise = page.waitForEvent('filechooser')
  await page.getByLabel('File', { exact: true }).click()
  await (await previewChooserPromise).setFiles(policyFile)
  await page.screenshot({ path: path.join(assets, 'desktop-library-upload-1440x900.png') })
  await library.getByRole('button', { name: 'Upload document' }).click()

  await library.getByRole('button', { name: 'New chat' }).click()
  await expect(page.getByRole('heading', { name: 'Ask about this document' })).toBeVisible()
  await page.getByRole('textbox', { name: 'Ask about this document' }).fill(question)

  const partialTextPromise = page.waitForFunction(() => {
    const article = document.querySelector('.workspace-assistant-message')
    return Boolean(article?.querySelector('.workspace-message-status') &&
      article?.querySelector('.workspace-assistant-body p')?.textContent?.trim())
  }, null, { timeout: 180_000, polling: 'raf' })
  const streamResponsePromise = page.waitForResponse(response =>
    /\/api\/chat\/\d+\/stream$/.test(response.url()) && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Send message' }).click()
  await partialTextPromise
  await expect(page.locator('.workspace-message-status')).toBeVisible()
  await page.screenshot({ path: path.join(assets, 'desktop-streaming-before-done-1440x900.png') })

  const streamResponse = await streamResponsePromise
  expect(streamResponse.status()).toBe(200)
  expect(streamResponse.headers()['content-type']).toContain('text/event-stream')
  const frames = parseSseFrames(await streamResponse.text())
  const tokenIndex = frames.findIndex(frame => frame.event === 'token' && frame.data.text)
  const doneIndex = frames.findIndex(frame => frame.event === 'done')
  expect(tokenIndex).toBeGreaterThanOrEqual(0)
  expect(doneIndex).toBeGreaterThan(tokenIndex)
  expect(frames.at(-1)?.event).toBe('done')
  const done = frames[doneIndex].data
  expect(done.answer_status).toBe('answered')
  expect(done.cited_sources.length).toBeGreaterThan(0)
  expect(done.cited_sources[0].document_id).toBe(uploaded.id)
  await expect(page.locator('.workspace-message-status')).toHaveCount(0)
  await expect(page.getByRole('button', { name: /Open source #/ })).toBeVisible()
  await expect(page.locator('.workspace-assistant-message')).toContainText('helpdesk ticket')
  await page.screenshot({ path: path.join(assets, 'desktop-english-qwen3-conversation-1440x900.png') })

  const sourceId = done.cited_sources[0].chunk_id
  const sourceResponsePromise = page.waitForResponse(response =>
    response.url() === `${baseURL}/api/documents/${uploaded.id}/chunks/${sourceId}`)
  await page.getByRole('button', { name: `Open source #${sourceId}` }).click()
  const sourceResponse = await sourceResponsePromise
  expect(sourceResponse.status()).toBe(200)
  const source = await sourceResponse.json()
  expect(source.chunk_id).toBe(sourceId)
  expect(source.document_id).toBe(uploaded.id)
  expect(source.document_title).toBe(title)
  expect(source.content).toContain('The helpdesk acknowledges the ticket within one business day.')
  await expect(page.getByRole('complementary', { name: 'Evidence viewer' })).toContainText(source.content)
  await page.screenshot({ path: path.join(assets, 'desktop-citation-evidence-1440x900.png') })

  await library.getByRole('button', { name: 'New chat' }).click()
  await expect(page.getByRole('heading', { name: 'Ask about this document' })).toBeVisible()
  const recent = page.getByRole('navigation', { name: 'Recent conversations' })
  await recent.getByRole('button', { name: question, exact: true }).click()
  await expect(page.locator('.workspace-user-message')).toHaveText(question)
  await expect(page.locator('.workspace-assistant-message')).toContainText('helpdesk ticket')
  await page.screenshot({ path: path.join(assets, 'desktop-conversation-history-1440x900.png') })

  await page.setViewportSize({ width: 390, height: 844 })
  await assertViewport(page, 390, 844)
  await expect(page.getByRole('main', { name: 'Policy assistant' })).toBeVisible()
  const chatWidths = await page.locator('.workspace-conversation').evaluate(element => ({
    scroll: element.scrollWidth,
    client: element.clientWidth,
  }))
  expect(chatWidths.scroll, `Mobile chat content must fit its viewport: ${JSON.stringify(chatWidths)}`)
    .toBeLessThanOrEqual(chatWidths.client + 1)
  await page.screenshot({ path: path.join(assets, 'mobile-workspace-390x844.png') })
  await page.getByRole('button', { name: 'Open library' }).click()
  await expect(library).toBeVisible()
  await expect(library.getByRole('button', { name: title, exact: false })).toBeVisible()
  await page.screenshot({ path: path.join(assets, 'mobile-library-390x844.png') })
  await page.getByRole('button', { name: 'Close library' }).click()
  await page.getByRole('button', { name: `Open source #${sourceId}` }).click()
  const evidence = page.getByRole('complementary', { name: 'Evidence viewer' })
  await expect(evidence).toBeVisible()
  await expect(evidence).toContainText('one business day')
  await page.screenshot({ path: path.join(assets, 'mobile-evidence-390x844.png') })
  await evidence.getByRole('button', { name: 'Close evidence' }).click()

  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await expect(page.getByRole('main', { name: 'Policy assistant' })).toHaveCount(0)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  console.log(`Browser acceptance passed: document ${uploaded.id}, ${frames.filter(frame => frame.event === 'token').length} SSE token events before done, source ${sourceId}.`)
})
