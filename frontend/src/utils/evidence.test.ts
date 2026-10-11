import { expect,test } from "vitest"
import { findExactOverlap } from "./evidence"

test("highlights only an exact substantial phrase shared with the answer",() => {
    const source = "Employees must obtain manager approval before working remotely."
    const answer = "Manager approval is required before working remotely [[chunk:1]]."
    const range = findExactOverlap(source,answer)
    expect(range).not.toBeNull()
    expect(source.slice(range!.start,range!.end)).toBe("before working remotely")
})

test("leaves the source unmarked without a substantial exact overlap",() => {
    expect(findExactOverlap("Employees may work at home.","Remote work is allowed [[chunk:1]]."))
        .toBeNull()
    expect(findExactOverlap("Employees may work at home.",null)).toBeNull()
})
