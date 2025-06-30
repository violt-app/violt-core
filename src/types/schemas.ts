// src/types/schemas.ts

export interface MorningEntryData {
  priority1: string;
  priority2?: string;
  priority3?: string;
  morningNotes?: string;
}

export interface EveningEntryData {
  accomplishments: string;
  challenges?: string;
  tomorrowFocus?: string;
  reflectionNotes?: string;
}

export interface DailyLog {
  _id?: string; // MongoDB document ID
  date: string; // YYYY-MM-DD
  userId?: string; // To associate data with a user
  morning?: MorningEntryData;
  evening?: EveningEntryData;
  aiInsights?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

// Existing schemas (assuming from the original page.tsx)
export interface DailySummary {
  day: string;
  summary: string;
  focus: string;
}

export interface ErrorSummary {
  title: string;
  description: string;
}
