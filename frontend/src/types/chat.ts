export type AnswerStatus = "answered" | "no_candidates" | "insufficient_evidence"
export type CitedSource = {chunk_id: number;document_id: number;chunk_index: number}
export type Conversation = {id: number;document_id: number;title: string | null;created_at: string;updated_at: string}
export type Message = {id: number | string;role: "user" | "assistant";content: string | null;answer_status: AnswerStatus | null;cited_chunk_ids: number[] | null;created_at?: string;pending?: boolean;failed?: boolean}
export type ConversationDetail = Conversation & {messages: Message[]}
export type StreamDone = {answer: string | null;answer_status: AnswerStatus;retrieval_status: string;cited_sources: CitedSource[]}
