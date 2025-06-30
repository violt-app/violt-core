"use server";

import clientPromise from '@/lib/mongodb';
import { DailyLog, MorningEntryData, EveningEntryData, DailySummary, ErrorSummary } from '@/types/schemas';
import { Collection, ObjectId } from 'mongodb';

// Helper function to get the 'dailylogs' collection
async function getDailyLogsCollection(): Promise<Collection<DailyLog>> {
  const client = await clientPromise;
  const db = client.db(); // Use your database name if you have one, otherwise it uses the default from the connection string
  return db.collection<DailyLog>('dailylogs');
}

export async function saveMorningEntry(
  date: string, // YYYY-MM-DD
  data: MorningEntryData,
  userId?: string // Optional: for multi-user support
): Promise<DailyLog | { error: string }> {
  try {
    const collection = await getDailyLogsCollection();
    const result = await collection.findOneAndUpdate(
      { date, userId }, // Filter
      {
        $set: {
          morning: data,
          date,
          userId, // Ensure userId is set if provided
          updatedAt: new Date()
        },
        $setOnInsert: { createdAt: new Date() } // Set createdAt only on insert
      }, // Update
      { upsert: true, returnDocument: 'after' } // Options: create if not exists, return the updated document
    );
    if (!result) { // result.value is deprecated, result itself contains the document or null
        return { error: 'Failed to save morning entry. Document not found after operation.' };
    }
    // MongoDB ObjectId needs to be converted to string for client-side usage if it's part of the return
    // However, result here is the full document, so _id will be an ObjectId.
    // For now, we assume the default DailyLog type handles _id appropriately if needed later.
    const updatedLog = result as DailyLog;

    // Attempt to generate AI insight if both morning and evening entries are present
    if (updatedLog.morning && updatedLog.evening) {
      await generateAndSaveAiInsight(updatedLog.date, updatedLog.userId);
    }
    // Re-fetch the log to include any AI insights
    return getDailyLog(date, userId) as Promise<DailyLog>; // Cast because getDailyLog can return null or error obj

  } catch (error) {
    console.error('Error saving morning entry:', error);
    return { error: 'Failed to save morning entry. Please try again.' };
  }
}

export async function saveEveningEntry(
  date: string, // YYYY-MM-DD
  data: EveningEntryData,
  userId?: string // Optional
): Promise<DailyLog | { error: string }> {
  try {
    const collection = await getDailyLogsCollection();
    const result = await collection.findOneAndUpdate(
      { date, userId },
      {
        $set: {
          evening: data,
          date,
          userId,
          updatedAt: new Date()
        },
        $setOnInsert: { createdAt: new Date() }
      },
      { upsert: true, returnDocument: 'after' }
    );
     if (!result) {
        return { error: 'Failed to save evening entry. Document not found after operation.' };
    }
    const updatedLog = result as DailyLog;

    // Attempt to generate AI insight if both morning and evening entries are present
    if (updatedLog.morning && updatedLog.evening) {
      await generateAndSaveAiInsight(updatedLog.date, updatedLog.userId);
    }
     // Re-fetch the log to include any AI insights
    return getDailyLog(date, userId) as Promise<DailyLog>; // Cast because getDailyLog can return null or error obj

  } catch (error) {
    console.error('Error saving evening entry:', error);
    return { error: 'Failed to save evening entry. Please try again.' };
  }
}

export async function getDailyLog(
  date: string, // YYYY-MM-DD
  userId?: string // Optional
): Promise<DailyLog | null | { error: string }> {
  try {
    const collection = await getDailyLogsCollection();
    const log = await collection.findOne({ date, userId });
    if (log && log._id) {
      // Ensure _id is a string if it's an ObjectId, though DailyLog type has _id as string.
      // The driver might return ObjectId, so conversion might be needed if issues arise.
      // For now, we'll cast. If `_id` is used directly and needs to be a string,
      // it should be `log._id.toHexString()`.
      return { ...log, _id: log._id.toString() } as DailyLog;
    }
    return null; // No log found for this date
  } catch (error) {
    console.error('Error fetching daily log:', error);
    return { error: 'Failed to fetch daily log. Please try again.' };
  }
}

// Placeholder for getWeeklyOverview as it was in the original page.tsx
// This would typically fetch and aggregate data for the week.
export async function getWeeklyOverview(
  currentDate: string, // YYYY-MM-DD format
  userId?: string // Optional
): Promise<DailySummary[] | ErrorSummary[]> {
  console.log('Fetching weekly overview for date:', currentDate, 'User ID:', userId);
  // Dummy implementation
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const exampleSummary: DailySummary[] = days.map(day => ({
    day,
    summary: `Summary for ${day}`,
    focus: `Focus for ${day}`
  }));

  // Simulate fetching real data for the week of `currentDate`
  // For now, return placeholder data
  // In a real scenario, you'd query MongoDB for entries around `currentDate`
  return exampleSummary;
  // Example error return:
  // return [{ title: 'Error', description: 'Could not load weekly overview.' }];
}

// AI Insight Generation Service
async function generateAiInsight(log: DailyLog): Promise<string> {
  // MOCK IMPLEMENTATION
  // In a real scenario, you would:
  // 1. Import and configure your Gemini SDK/client here.
  //    const { GoogleGenerativeAI } = require("@google/generative-ai");
  //    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
  //    const model = genAI.getGenerativeModel({ model: "gemini-pro" }); // Or your chosen model

  // 2. Construct a detailed prompt based on the log data.
  let prompt = `Analyze the following daily log and provide a concise insight or suggestion.\n\n`;
  if (log.morning) {
    prompt += `Morning Priorities:\n- ${log.morning.priority1}\n`;
    if (log.morning.priority2) prompt += `- ${log.morning.priority2}\n`;
    if (log.morning.priority3) prompt += `- ${log.morning.priority3}\n`;
    if (log.morning.morningNotes) prompt += `Morning Notes: ${log.morning.morningNotes}\n`;
  }
  if (log.evening) {
    prompt += `\nEvening Reflection:\nAccomplishments: ${log.evening.accomplishments}\n`;
    if (log.evening.challenges) prompt += `Challenges: ${log.evening.challenges}\n`;
    if (log.evening.tomorrowFocus) prompt += `Focus for Tomorrow: ${log.evening.tomorrowFocus}\n`;
    if (log.evening.reflectionNotes) prompt += `Reflection Notes: ${log.evening.reflectionNotes}\n`;
  }
  prompt += "\nInsight:";

  console.log("Generated Prompt for AI:", prompt); // For debugging

  // 3. Call the Gemini API.
  //    try {
  //      const result = await model.generateContent(prompt);
  //      const response = await result.response;
  //      const text = response.text();
  //      return text;
  //    } catch (error) {
  //      console.error("Error calling Gemini API:", error);
  //      return "Could not generate AI insight at this time.";
  //    }

  // Mocked response:
  await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call delay
  const insights = [
    "Remember to take short breaks throughout the day to maintain focus on your priorities.",
    "Consider breaking down your top priority into smaller, more manageable tasks.",
    "Your evening reflections show good progress. Keep up the momentum for tomorrow!",
    "Noticing a pattern in your challenges? Perhaps dedicate some time to address the root cause.",
    "It's great that you're planning for tomorrow. This proactive approach is beneficial."
  ];
  return insights[Math.floor(Math.random() * insights.length)];
}

export async function generateAndSaveAiInsight(
  date: string,
  userId?: string
): Promise<void> {
  try {
    const collection = await getDailyLogsCollection();
    const log = await collection.findOne({ date, userId });

    if (log && log.morning && log.evening) {
      // Only generate insight if not already present or if we want to regenerate
      // For now, let's assume we always regenerate if called.
      // A more sophisticated approach might check if insights are stale or missing.

      const insightText = await generateAiInsight(log);

      await collection.updateOne(
        { _id: log._id },
        { $set: { aiInsights: insightText, updatedAt: new Date() } }
      );
      console.log(`AI insight generated and saved for log date: ${date}, user: ${userId || 'default'}`);
    }
  } catch (error) {
    console.error('Error generating or saving AI insight:', error);
    // Decide if this error should propagate or be handled silently
  }
}
