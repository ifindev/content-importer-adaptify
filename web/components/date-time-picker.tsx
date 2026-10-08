"use client";

import { CalendarDays } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

function pad(n: number) {
  return String(n).padStart(2, "0");
}

/** "YYYY-MM-DDTHH:mm" is local wall time, so the strings sort like dates. */
function splitValue(value: string) {
  const [date = "", time = ""] = value.split("T");
  return { date, time };
}

function splitTime(time: string) {
  const [h = "00", m = "00"] = time.split(":");
  return { hour: Number(h), minute: Number(m) };
}

function toDate(date: string) {
  const [y = 0, m = 1, d = 1] = date.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toDateString(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const HOURS = Array.from({ length: 24 }, (_, h) => h);
const MINUTES = Array.from({ length: 60 }, (_, m) => m);

type Option = { value: number; disabled: boolean };

/**
 * One scrolling column of numbers (hours or minutes). A native <select>
 * opens a screen-tall menu that CSS can't cap, so the list is our own.
 * Opens scrolled to the chosen number; the arrow keys skip disabled ones.
 */
function Column({
  label,
  options,
  selected,
  onPick,
}: {
  label: string;
  options: Option[];
  selected: number;
  onPick: (value: number) => void;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const list = listRef.current;
    const chosen = list?.querySelector<HTMLElement>("[aria-selected=true]");
    if (list && chosen) {
      list.scrollTop = chosen.offsetTop - list.clientHeight / 2;
    }
    // Only on open: later picks shouldn't make the list jump.
  }, []);

  function move(e: React.KeyboardEvent<HTMLButtonElement>, step: 1 | -1) {
    e.preventDefault();
    let next = e.currentTarget as Element | null;
    do {
      next =
        step === 1 ? next!.nextElementSibling : next!.previousElementSibling;
    } while (next instanceof HTMLButtonElement && next.disabled);
    if (next instanceof HTMLButtonElement) next.focus();
  }

  return (
    <div
      ref={listRef}
      role="listbox"
      aria-label={label}
      className="relative flex max-h-36 w-[4.5rem] flex-col gap-px overflow-y-auto rounded-lg border p-1 sm:max-h-[17.5rem]"
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="option"
          aria-selected={o.value === selected}
          disabled={o.disabled}
          tabIndex={o.value === selected ? 0 : -1}
          onClick={() => onPick(o.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") move(e, 1);
            if (e.key === "ArrowUp") move(e, -1);
          }}
          className={cn(
            "focus-visible:ring-ring/50 h-8 shrink-0 rounded-md text-[13px] tabular-nums outline-none focus-visible:ring-3 max-lg:h-10 max-lg:text-[15px]",
            o.disabled ? "text-faint cursor-not-allowed" : "hover:bg-muted",
            o.value === selected &&
              "bg-primary text-primary-foreground hover:bg-primary",
          )}
        >
          {pad(o.value)}
        </button>
      ))}
    </div>
  );
}

/**
 * A date and time picker with a lower limit. Days, hours and minutes before
 * `min` are disabled: plain faint text, not boxes. `value` and `min` are
 * local "YYYY-MM-DDTHH:mm" strings.
 */
export function DateTimePicker({
  id,
  name,
  value,
  min,
  onChange,
  invalid,
}: {
  id: string;
  name?: string;
  value: string;
  min: string;
  onChange: (value: string) => void;
  invalid?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const { date, time } = splitValue(value);
  const { date: minDate, time: minTime } = splitValue(min);
  const selected = date ? toDate(date) : undefined;
  const { hour, minute } = splitTime(time || "00:00");
  const min_ = splitTime(minTime || "00:00");
  const onMinDay = date !== "" && date === minDate;

  function pickDay(day: Date | undefined) {
    if (!day) return;
    const picked = toDateString(day);
    // On the first allowed day, an earlier time moves up to the first
    // allowed time instead of leaving an invalid pair.
    const nextTime = picked === minDate && time < minTime ? minTime : time;
    onChange(`${picked}T${nextTime || "00:00"}`);
  }

  function pickHour(h: number) {
    // Landing on the first allowed hour with too early a minute: move the
    // minute up to the first allowed one.
    const m =
      onMinDay && h === min_.hour && minute < min_.minute
        ? min_.minute
        : minute;
    onChange(`${date}T${pad(h)}:${pad(m)}`);
  }

  function pickMinute(m: number) {
    onChange(`${date}T${pad(hour)}:${pad(m)}`);
  }

  const hourOptions: Option[] = HOURS.map((h) => ({
    value: h,
    disabled: !date || (onMinDay && h < min_.hour),
  }));
  const atMinHour = onMinDay && hour === min_.hour;
  const minuteOptionsList: Option[] = MINUTES.map((m) => ({
    value: m,
    disabled: !date || (atMinHour && m < min_.minute),
  }));

  const label = selected
    ? new Date(`${date}T${time || "00:00"}`).toLocaleString(undefined, {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })
    : "Pick a date and time";

  return (
    <>
      {name && <input type="hidden" name={name} value={value} />}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={
            <Button
              id={id}
              type="button"
              variant="outline"
              aria-invalid={invalid || undefined}
              className={cn(
                "w-full justify-start font-normal max-lg:h-10 max-lg:text-[15px]",
                invalid && "border-destructive",
              )}
            />
          }
        >
          <CalendarDays className="text-faint" />
          {label}
        </PopoverTrigger>
        <PopoverContent
          align="start"
          className="w-auto flex-col gap-2 p-2 sm:flex-row"
        >
          <Calendar
            mode="single"
            selected={selected}
            onSelect={pickDay}
            defaultMonth={selected}
            startMonth={minDate ? toDate(minDate) : undefined}
            disabled={minDate ? { before: toDate(minDate) } : undefined}
          />
          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground px-1 text-[12.5px]">
              Time
            </span>
            <div className="flex gap-2">
              <Column
                label="Hour"
                options={hourOptions}
                selected={hour}
                onPick={pickHour}
              />
              <Column
                label="Minute"
                options={minuteOptionsList}
                selected={minute}
                onPick={pickMinute}
              />
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </>
  );
}
