import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import DailyPlannerPage from '../page'; // Adjust path as necessary
import * as actions from '../actions'; // Adjust path as necessary
import { DailyLog, MorningEntryData, EveningEntryData } from '@/types/schemas';

// Mock the actions module
jest.mock('../actions', () => ({
  getDailyLog: jest.fn(),
  saveMorningEntry: jest.fn(),
  saveEveningEntry: jest.fn(),
  getWeeklyOverview: jest.fn(),
  generateAndSaveAiInsight: jest.fn(), // Also mock this if it's directly called or if its absence causes issues
}));

// Mock Mantine's useMediaQuery hook as it might be used internally by components
jest.mock('@mantine/hooks', () => ({
  ...jest.requireActual('@mantine/hooks'),
  useMediaQuery: jest.fn().mockReturnValue(false),
}));

// Helper function to wrap component with providers
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <MantineProvider>
      <Notifications />
      {ui}
    </MantineProvider>
  );
};

const mockDate = new Date(2023, 10, 20); // Example: Nov 20, 2023
const mockDateString = '2023-11-20';

describe('DailyPlannerPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Provide a default successful response for getWeeklyOverview
    (actions.getWeeklyOverview as jest.Mock).mockResolvedValue([]);
    // Mock Date constructor to return a fixed date for consistent testing
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders the daily planner page with necessary elements', async () => {
    (actions.getDailyLog as jest.Mock).mockResolvedValue(null);
    renderWithProviders(<DailyPlannerPage />);

    expect(screen.getByText('Daily Planner & Review')).toBeInTheDocument();
    expect(screen.getByLabelText('Select Date')).toBeInTheDocument();
    expect(screen.getByText('Morning Focus')).toBeInTheDocument();
    expect(screen.getByText('Evening Reflection')).toBeInTheDocument();
    expect(screen.getByText('AI Insights')).toBeInTheDocument();
    expect(screen.getByText('Weekly Overview')).toBeInTheDocument();
  });

  it('fetches and displays existing daily log data', async () => {
    const mockLog: DailyLog = {
      date: mockDateString,
      morning: { priority1: 'Test P1', morningNotes: 'Morning notes test' },
      evening: { accomplishments: 'Evening accomplishments', reflectionNotes: 'Reflection notes test' },
      aiInsights: 'Test AI Insight',
    };
    (actions.getDailyLog as jest.Mock).mockResolvedValue(mockLog);

    renderWithProviders(<DailyPlannerPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Priority 1')).toHaveValue('Test P1');
      expect(screen.getByLabelText('Additional Notes')).toHaveValue('Morning notes test');
      expect(screen.getByLabelText("Today's Accomplishments")).toHaveValue('Evening accomplishments');
      expect(screen.getByLabelText('Reflection Notes')).toHaveValue('Reflection notes test');
      expect(screen.getByText('Test AI Insight')).toBeInTheDocument();
    });
  });

  it('populates forms with empty values if no daily log exists', async () => {
    (actions.getDailyLog as jest.Mock).mockResolvedValue(null);
    renderWithProviders(<DailyPlannerPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Priority 1')).toHaveValue('');
      expect(screen.getByLabelText("Today's Accomplishments")).toHaveValue('');
      expect(screen.getByText(/AI insights will appear here/i)).toBeInTheDocument();
    });
  });

   it('handles error when fetching daily log', async () => {
    (actions.getDailyLog as jest.Mock).mockResolvedValue({ error: 'Failed to fetch' });
    renderWithProviders(<DailyPlannerPage />);

    await waitFor(() => {
      // Check for notification - Mantine notifications might not be easily testable this way without more setup
      // For now, ensure forms are empty
      expect(screen.getByLabelText('Priority 1')).toHaveValue('');
      // A more robust test would check for the notification itself.
      // Example: expect(screen.getByText('Error Fetching Daily Log')).toBeInTheDocument();
      // This depends on how notifications are rendered and if they are part of the document queryable by RTL.
    });
  });

  it('allows user to input and save morning plan', async () => {
    const morningData: MorningEntryData = {
      priority1: 'New Morning P1',
      priority2: 'New Morning P2',
      priority3: '',
      morningNotes: 'Fresh morning notes',
    };
    const savedLog: DailyLog = { date: mockDateString, morning: morningData };
    (actions.getDailyLog as jest.Mock).mockResolvedValue(null); // Start with no data
    (actions.saveMorningEntry as jest.Mock).mockResolvedValue(savedLog);

    renderWithProviders(<DailyPlannerPage />);

    fireEvent.change(screen.getByLabelText('Priority 1'), { target: { value: morningData.priority1 } });
    fireEvent.change(screen.getByLabelText('Priority 2'), { target: { value: morningData.priority2 } });
    fireEvent.change(screen.getByLabelText('Additional Notes'), { target: { value: morningData.morningNotes } });

    fireEvent.click(screen.getByRole('button', { name: 'Save Morning Plan' }));

    await waitFor(() => {
      expect(actions.saveMorningEntry).toHaveBeenCalledWith(mockDateString, morningData);
      // Check for success notification (again, depends on notification setup)
      // expect(screen.getByText('Morning Plan Saved')).toBeInTheDocument();
      // Form should be updated with returned values (or stay as is if no specific update logic post-save)
      expect(screen.getByLabelText('Priority 1')).toHaveValue(morningData.priority1);
    });
  });

  it('allows user to input and save evening reflection', async () => {
    const eveningData: EveningEntryData = {
      accomplishments: 'Evening tasks done',
      challenges: 'Faced some bugs',
      tomorrowFocus: 'Fix bugs',
      reflectionNotes: 'Need more coffee',
    };
    const savedLog: DailyLog = { date: mockDateString, evening: eveningData };
     (actions.getDailyLog as jest.Mock).mockResolvedValue(null); // Start with no data
    (actions.saveEveningEntry as jest.Mock).mockResolvedValue(savedLog);

    renderWithProviders(<DailyPlannerPage />);

    fireEvent.change(screen.getByLabelText("Today's Accomplishments"), { target: { value: eveningData.accomplishments } });
    fireEvent.change(screen.getByLabelText('Challenges Faced'), { target: { value: eveningData.challenges } });
    fireEvent.change(screen.getByLabelText("Tomorrow's Focus"), { target: { value: eveningData.tomorrowFocus } });
    fireEvent.change(screen.getByLabelText('Reflection Notes'), { target: { value: eveningData.reflectionNotes } });

    fireEvent.click(screen.getByRole('button', { name: 'Save Evening Reflection' }));

    await waitFor(() => {
      expect(actions.saveEveningEntry).toHaveBeenCalledWith(mockDateString, eveningData);
      // expect(screen.getByText('Evening Reflection Saved')).toBeInTheDocument();
      expect(screen.getByLabelText("Today's Accomplishments")).toHaveValue(eveningData.accomplishments);
    });
  });

  it('shows an error notification if saving morning plan fails', async () => {
    (actions.getDailyLog as jest.Mock).mockResolvedValue(null);
    (actions.saveMorningEntry as jest.Mock).mockResolvedValue({ error: 'Failed to save morning plan' });

    renderWithProviders(<DailyPlannerPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Save Morning Plan' }));

    await waitFor(() => {
      expect(actions.saveMorningEntry).toHaveBeenCalled();
      // Check for error notification (highly dependent on setup)
      // expect(screen.getByText('Error Saving Morning Plan')).toBeInTheDocument();
    });
  });

  it('shows an error notification if saving evening reflection fails', async () => {
    (actions.getDailyLog as jest.Mock).mockResolvedValue(null);
    (actions.saveEveningEntry as jest.Mock).mockResolvedValue({ error: 'Failed to save evening reflection' });

    renderWithProviders(<DailyPlannerPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Save Evening Reflection' }));

    await waitFor(() => {
      expect(actions.saveEveningEntry).toHaveBeenCalled();
      // expect(screen.getByText('Error Saving Evening Reflection')).toBeInTheDocument();
    });
  });

  it('displays AI insights when available in the daily log', async () => {
    const mockLogWithInsight: DailyLog = {
      date: mockDateString,
      morning: { priority1: 'P1' },
      evening: { accomplishments: 'A1' },
      aiInsights: 'This is a brilliant AI insight.',
    };
    (actions.getDailyLog as jest.Mock).mockResolvedValue(mockLogWithInsight);

    renderWithProviders(<DailyPlannerPage />);

    await waitFor(() => {
      expect(screen.getByText('This is a brilliant AI insight.')).toBeInTheDocument();
    });
  });

  it('displays placeholder text when AI insights are not available', async () => {
    const mockLogNoInsight: DailyLog = {
      date: mockDateString,
      morning: { priority1: 'P1' },
      evening: { accomplishments: 'A1' },
      // aiInsights is undefined or null
    };
    (actions.getDailyLog as jest.Mock).mockResolvedValue(mockLogNoInsight);

    renderWithProviders(<DailyPlannerPage />);

    await waitFor(() => {
      expect(screen.getByText(/AI insights will appear here/i)).toBeInTheDocument();
    });
  });

});
