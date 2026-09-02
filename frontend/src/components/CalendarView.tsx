import { useMemo, useState } from "react";

import { useI18n } from "../i18n";
import type { Activity } from "../types";

interface Props {
  activities: Activity[];
}

const WEEKDAY_KEYS = [
  "weekday.sun",
  "weekday.mon",
  "weekday.tue",
  "weekday.wed",
  "weekday.thu",
  "weekday.fri",
  "weekday.sat",
] as const;

function monthLabel(value: string, lang: string): string {
  const [year, month] = value.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString(lang === "fa" ? "fa-IR" : lang, {
    month: "long",
    year: "numeric",
  });
}

export default function CalendarView({ activities }: Props) {
  const { t, lang } = useI18n();
  const initialMonth = activities.at(-1)?.date.slice(0, 7) ?? new Date().toISOString().slice(0, 7);
  const [month, setMonth] = useState(initialMonth);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [year, monthNumber] = month.split("-").map(Number);
  const daysInMonth = new Date(year, monthNumber, 0).getDate();
  const firstDay = new Date(year, monthNumber - 1, 1).getDay();

  const byDate = useMemo(() => {
    const map = new Map<string, Activity[]>();
    for (const activity of activities) {
      const items = map.get(activity.date) ?? [];
      items.push(activity);
      map.set(activity.date, items);
    }
    return map;
  }, [activities]);

  function moveMonth(offset: number) {
    const date = new Date(year, monthNumber - 1 + offset, 1);
    setMonth(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`);
    setSelectedDate(null);
  }

  const selected = selectedDate ? (byDate.get(selectedDate) ?? []) : [];

  return (
    <section className="dashboard-card calendar-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">{t("calendar.eyebrow")}</p>
          <h2>{monthLabel(month, lang)}</h2>
        </div>
        <div className="calendar-nav">
          <button type="button" onClick={() => moveMonth(-1)} aria-label={t("calendar.prevMonth")}>
            ←
          </button>
          <button type="button" onClick={() => moveMonth(1)} aria-label={t("calendar.nextMonth")}>
            →
          </button>
        </div>
      </div>
      <div className="calendar-weekdays">
        {WEEKDAY_KEYS.map((dayKey) => (
          <span key={dayKey}>{t(dayKey)}</span>
        ))}
      </div>
      <div className="calendar-grid">
        {Array.from({ length: firstDay }).map((_, index) => (
          <span className="calendar-empty" key={`empty-${index}`} />
        ))}
        {Array.from({ length: daysInMonth }).map((_, index) => {
          const day = index + 1;
          const date = `${year}-${String(monthNumber).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const count = byDate.get(date)?.length ?? 0;
          return (
            <button
              type="button"
              className={`calendar-day ${selectedDate === date ? "selected" : ""}`}
              key={date}
              aria-label={`${date}, ${count} ${count === 1 ? t("calendar.activity") : t("calendar.activities")}`}
              onClick={() => setSelectedDate(date)}
            >
              <span>{day}</span>
              {count > 0 ? <strong>{count}</strong> : null}
            </button>
          );
        })}
      </div>
      {selectedDate ? (
        <div className="calendar-detail">
          <strong>{selectedDate}</strong>
          {selected.length ? (
            selected.map((activity) => (
              <p key={activity.id}>
                <span className={`status-dot ${activity.status}`} />
                {activity.title}
              </p>
            ))
          ) : (
            <p>{t("calendar.noActivities")}</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
