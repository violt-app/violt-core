"use client";

import { useEffect, useState } from 'react';
import { TextInput, Button, Paper, Title, Text, Container, Group, Textarea, Card, Grid, Timeline, ActionIcon, LoadingOverlay } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconMicrophone, IconX } from '@tabler/icons-react';
import { getWeeklyOverview, saveMorningEntry, saveEveningEntry, getDailyLog } from './actions';
import { DailySummary, ErrorSummary, DailyLog, MorningEntryData, EveningEntryData } from "@/types/schemas";

// Helper to format date to YYYY-MM-DD
const formatDateToYYYYMMDD = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

export default function DailyPlannerPage() {
  const [date, setDate] = useState<Date | null>(new Date());
  const [isRecording, setIsRecording] = useState(false);
  const [weeklyOverview, setWeeklyOverview] = useState<DailySummary[] | ErrorSummary[]>([]);
  const [loadingWeeklySummary, setLoadingWeeklySummary] = useState(false);
  const [dailyLog, setDailyLog] = useState<DailyLog | null>(null);
  const [loadingDailyLog, setLoadingDailyLog] = useState(false);
  const [savingMorning, setSavingMorning] = useState(false);
  const [savingEvening, setSavingEvening] = useState(false);

  const morningFormInitialValues: MorningEntryData = {
    priority1: '',
    priority2: '',
    priority3: '',
    morningNotes: '',
  };

  const eveningFormInitialValues: EveningEntryData = {
    accomplishments: '',
    challenges: '',
    tomorrowFocus: '',
    reflectionNotes: '',
  };

  const morningForm = useForm({ initialValues: morningFormInitialValues });
  const eveningForm = useForm({ initialValues: eveningFormInitialValues });

  // Fetch Daily Log when date changes
  useEffect(() => {
    if (!date) {
      setDailyLog(null);
      morningForm.reset(); // Resets to initialValues
      eveningForm.reset(); // Resets to initialValues
      return;
    }

    setLoadingDailyLog(true);
    const dateString = formatDateToYYYYMMDD(date);

    getDailyLog(dateString)
      .then(log => {
        if (log && 'error' in log) {
          notifications.show({
            title: 'Error Fetching Daily Log',
            message: log.error,
            color: 'red',
            icon: <IconX size="1.1rem" />,
          });
          setDailyLog(null);
          morningForm.reset();
          eveningForm.reset();
        } else if (log) {
          setDailyLog(log);
          morningForm.setValues(log.morning || morningFormInitialValues);
          eveningForm.setValues(log.evening || eveningFormInitialValues);
        } else { // No log found, not an error
          setDailyLog(null);
          morningForm.reset();
          eveningForm.reset();
        }
      })
      .catch(error => {
        console.error('Error fetching daily log:', error);
        notifications.show({
          title: 'Error',
          message: 'Failed to fetch daily log. Please try again.',
          color: 'red',
          icon: <IconX size="1.1rem" />,
        });
        setDailyLog(null);
        morningForm.reset();
        eveningForm.reset();
      })
      .finally(() => setLoadingDailyLog(false));

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  // Fetch Weekly Overview (existing logic)
  useEffect(() => {
    if (!date) return;
    setLoadingWeeklySummary(true);
    const dateString = formatDateToYYYYMMDD(date);
    getWeeklyOverview(dateString)
      .then(setWeeklyOverview)
      .catch(error => {
        console.error('Error fetching weekly overview:', error);
        setWeeklyOverview([{
          title: 'Error',
          description: 'Failed to load weekly overview. Please try again later.'
        }]);
      })
      .finally(() => setLoadingWeeklySummary(false));
  }, [date]);

  const handleMorningSubmit = async (values: MorningEntryData) => {
    if (!date) return;
    setSavingMorning(true);
    const dateString = formatDateToYYYYMMDD(date);
    const result = await saveMorningEntry(dateString, values);

    if (result && 'error' in result) {
      notifications.show({
        title: 'Error Saving Morning Plan',
        message: result.error,
        color: 'red',
        icon: <IconX size="1.1rem" />,
      });
    } else if (result) {
      notifications.show({
        title: 'Morning Plan Saved',
        message: 'Your morning priorities have been saved successfully!',
        color: 'green',
        icon: <IconCheck size="1.1rem" />,
      });
      // Update dailyLog state with the new/updated morning entry
      // The result from saveMorningEntry is the complete DailyLog document
      setDailyLog(result);
      if (result.morning) morningForm.setValues(result.morning);
    }
    setSavingMorning(false);
  };

  const handleEveningSubmit = async (values: EveningEntryData) => {
    if (!date) return;
    setSavingEvening(true);
    const dateString = formatDateToYYYYMMDD(date);
    const result = await saveEveningEntry(dateString, values);

    if (result && 'error' in result) {
      notifications.show({
        title: 'Error Saving Evening Reflection',
        message: result.error,
        color: 'red',
        icon: <IconX size="1.1rem" />,
      });
    } else if (result) {
      notifications.show({
        title: 'Evening Reflection Saved',
        message: 'Your evening reflection has been saved successfully!',
        color: 'green',
        icon: <IconCheck size="1.1rem" />,
      });
      // Update dailyLog state with the new/updated evening entry
      setDailyLog(result);
      if (result.evening) eveningForm.setValues(result.evening);
    }
    setSavingEvening(false);
  };

  const toggleVoiceRecording = () => {
    setIsRecording(!isRecording);
    notifications.show({
      title: isRecording ? 'Voice Recording Stopped' : 'Voice Recording Started',
      message: isRecording ? 'Your voice input has been processed (simulated).' : 'Speak now to record your input (simulated).',
      color: 'blue',
    });
  };

  const handleDateChange = (newDate: Date | null) => {
    setDate(newDate);
  };

  const getTodayIndex = () => {
    const currentDate = date || new Date();
    return currentDate.getDay();
  };

  return (
    <Container size="lg" mt="80">
      <LoadingOverlay visible={loadingDailyLog} overlayProps={{ radius: "sm", blur: 2 }} />
      <Title order={1} mb="md">Daily Planner & Review</Title>

      <Group justify="space-between" mb="xl">
        <DatePickerInput
          value={date}
          onChange={handleDateChange}
          label="Select Date"
          placeholder="Pick a date"
          mx="auto"
          maw={400}
          popoverProps={{ withinPortal: true }} // Good for modals/drawers
        />
      </Group>

      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" p="lg" radius="md" withBorder mb="xl" style={{ position: 'relative' }}>
            <LoadingOverlay visible={savingMorning} overlayProps={{ radius: "sm", blur: 2 }} />
            <Title order={2} mb="md">Morning Focus</Title>
            <form onSubmit={morningForm.onSubmit(handleMorningSubmit)}>
              <TextInput
                label="Priority 1"
                placeholder="Your most important task today"
                required
                mb="md"
                {...morningForm.getInputProps('priority1')}
              />
              <TextInput
                label="Priority 2"
                placeholder="Your second priority"
                mb="md"
                {...morningForm.getInputProps('priority2')}
              />
              <TextInput
                label="Priority 3"
                placeholder="Your third priority"
                mb="md"
                {...morningForm.getInputProps('priority3')}
              />
              <Group justify="right" mb="md">
                <ActionIcon
                  onClick={toggleVoiceRecording}
                  variant={isRecording ? "filled" : "outline"}
                  color={isRecording ? "red" : "blue"}
                  size="xl"
                  radius="xl"
                  aria-label={isRecording ? "Stop Recording" : "Start Recording"}
                >
                  <IconMicrophone size="1.5rem" />
                </ActionIcon>
              </Group>
              <Textarea
                label="Additional Notes"
                placeholder="Any other thoughts for the day"
                minRows={3}
                mb="md"
                {...morningForm.getInputProps('morningNotes')}
              />
              <Button type="submit" fullWidth mt="md" loading={savingMorning}>
                Save Morning Plan
              </Button>
            </form>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" p="lg" radius="md" withBorder mb="xl" style={{ position: 'relative' }}>
            <LoadingOverlay visible={savingEvening} overlayProps={{ radius: "sm", blur: 2 }} />
            <Title order={2} mb="md">Evening Reflection</Title>
            <form onSubmit={eveningForm.onSubmit(handleEveningSubmit)}>
              <Textarea
                label="Today's Accomplishments"
                placeholder="What did you accomplish today?"
                minRows={2}
                mb="md"
                required
                {...eveningForm.getInputProps('accomplishments')}
              />
              <Textarea
                label="Challenges Faced"
                placeholder="What challenges did you encounter?"
                minRows={2}
                mb="md"
                {...eveningForm.getInputProps('challenges')}
              />
              <Textarea
                label="Tomorrow's Focus"
                placeholder="What will you focus on tomorrow?"
                minRows={2}
                mb="md"
                {...eveningForm.getInputProps('tomorrowFocus')}
              />
              <Group justify="right" mb="md">
                <ActionIcon
                  onClick={toggleVoiceRecording}
                  variant={isRecording ? "filled" : "outline"}
                  color={isRecording ? "red" : "blue"}
                  size="xl"
                  radius="xl"
                  aria-label={isRecording ? "Stop Recording" : "Start Recording"}
                >
                  <IconMicrophone size="1.5rem" />
                </ActionIcon>
              </Group>
              <Textarea
                label="Reflection Notes"
                placeholder="Any other reflections on your day"
                minRows={3}
                mb="md"
                {...eveningForm.getInputProps('reflectionNotes')}
              />
              <Button type="submit" fullWidth mt="md" loading={savingEvening}>
                Save Evening Reflection
              </Button>
            </form>
          </Card>
        </Grid.Col>
      </Grid>

      <Card shadow="sm" p="lg" radius="md" withBorder mb="xl">
        <Title order={2} mb="md">AI Insights</Title>
        {dailyLog?.aiInsights ? (
          <Paper withBorder p="md" radius="md" style={{ whiteSpace: 'pre-wrap' }}>
            <Text>{dailyLog.aiInsights}</Text>
          </Paper>
        ) : (
          <Text color="dimmed" mb="md">
            AI insights will appear here after you save your plans and reflections.
            The AI will process your entries and provide feedback once available.
          </Text>
        )}
      </Card>

      <Card shadow="sm" p="lg" radius="md" withBorder>
        <Title order={2} mb="md">Weekly Overview</Title>
        <LoadingOverlay visible={loadingWeeklySummary} overlayProps={{ radius: "sm", blur: 1 }} />
        {weeklyOverview.length > 0 ? (
          <Timeline active={getTodayIndex()} bulletSize={24} lineWidth={2}>
            {weeklyOverview.map((item, idx) => {
              if ('day' in item) { // DailySummary
                return (
                  <Timeline.Item key={item.day || idx} title={item.day}>
                    <Text c="dimmed" size="sm">{item.summary}</Text>
                    <Text size="xs" mt={4}>Focus: {item.focus}</Text>
                  </Timeline.Item>
                );
              }
              // ErrorSummary
              return (
                <Timeline.Item key={idx} title={item.title} color="red" bullet={<IconX size={12} />}>
                  <Text c="dimmed" size="sm">{item.description}</Text>
                </Timeline.Item>
              );
            })}
          </Timeline>
        ) : (
          !loadingWeeklySummary && <Text color="dimmed">No weekly overview data available for this period.</Text>
        )}
      </Card>
    </Container>
  );
}
