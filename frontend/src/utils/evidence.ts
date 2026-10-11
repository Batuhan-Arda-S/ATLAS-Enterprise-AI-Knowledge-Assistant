type Word = {value: string;start: number;end: number}

function words(text: string): Word[] {
    return [...text.matchAll(/[\p{L}\p{N}]+/gu)].map(match => ({
        value:match[0].toLocaleLowerCase(),
        start:match.index,
        end:match.index + match[0].length,
    }))
}

export function findExactOverlap(source: string,answer: string | null): {start: number;end: number} | null {
    if (!answer) return null
    const sourceWords = words(source)
    const cleanAnswer = answer.replace(/\[\[chunk:\d+\]\]/g," ")
    const answerWords = words(cleanAnswer)
    let best: {start: number;end: number} | null = null
    for (let i = 0; i < sourceWords.length; i++) {
        for (let j = 0; j < answerWords.length; j++) {
            let count = 0
            while (i + count < sourceWords.length && j + count < answerWords.length &&
                sourceWords[i + count].value === answerWords[j + count].value) count++
            if (count < 3) continue
            const start = sourceWords[i].start
            const end = sourceWords[i + count - 1].end
            if (end - start < 18 || !cleanAnswer.toLocaleLowerCase().includes(
                source.slice(start,end).toLocaleLowerCase()) ||
                best && end - start <= best.end - best.start) continue
            best = {start,end}
        }
    }
    return best
}
