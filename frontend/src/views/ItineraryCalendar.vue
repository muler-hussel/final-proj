<template>
  <div class="flex p-4 h-screen">
    <div class="w-7/10 p-4 scroll-container">
      <FullCalendar
        ref="calendarRef"
        :options="calendarOptions"
      />
    </div>
    <div 
      class="w-3/10 p-4 bg-gray-50 overflow-y-auto"
    >
      <h3 class="font-bold mb-4">Shortlist</h3>
      <div 
        v-for="place in shortlist" 
        :key="place.id"
        draggable="true"
        @dragstart="handleDragStart($event, place)"
        class="mb-2 p-3 bg-white rounded shadow cursor-move fc-draggable"
        :data-transfer="JSON.stringify(place)"
      >
        {{ place.name }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin, { Draggable } from '@fullcalendar/interaction';
import type { CalendarOptions, EventApi } from '@fullcalendar/core';
import type { EventReceiveArg, EventDragStopArg } from '@fullcalendar/interaction';

// Customize Header as Day 1, Day 2, Day 3
const formatDayHeader = (date: Date) => {
  const startDate = Date.now();
  const diffDays = Math.floor((+date - +startDate) / (1000 * 60 * 60 * 24)) + 2;
  return `Day ${diffDays}`;
};

const addDays = (date: Date, days: number) => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

const calendarRef = ref();
const currentDateRange = ref({ start: new Date(), end: addDays(new Date(), 4) });

interface Place {
  id: string;
  name: string;
  duration: number; //Hours
}

const shortlist = ref<Place[]>([
  { id: 'p1', name: 'Museum of The Future', duration: 2 },
  { id: 'p2', name: 'Burj Khalifa', duration: 1.5 }
]);

// Drag from shortlist to calendar
const handleDragStart = (e: DragEvent, place: Place) => {
  if (!e.dataTransfer) return;
  e.dataTransfer.setData('text/plain', JSON.stringify(place));
};

// Calendar receive from shortlist
const handleEventReceive = (info: EventReceiveArg) => {
  if (!info.draggedEl.dataset.transfer) return;
  const place = JSON.parse(info.draggedEl.dataset.transfer);
  console.log(place);
  
  // 设置事件属性
  info.event.setProp('title', place.name);
  info.event.setExtendedProp('placeId', place.id);
  
  // 固定持续时间（如2小时）
  if (!info.event.start) return;
  const end = new Date(info.event.start);
  end.setHours(end.getHours() + place.duration);
  info.event.setEnd(end);
  
  // 从 shortlist 移除（可选）
  shortlist.value = shortlist.value.filter(p => p.id !== place.id);
};

// Shortlist receive from calendar
const handleDropFromCalendar = (event: EventApi) => {
  if (event && event.end && event.start) {
    shortlist.value.push({
      id: event.id,
      name: event.title,
      duration: (+event.end - +event.start) / 3600000
    });
    event.remove();
  }
};

// Handle with drags stopping inside of shortlist area
const handleDragStop = (info: EventDragStopArg) => {
  const { jsEvent, event } = info;
  const shortlistDiv = document.querySelector('.w-3\\/10.p-4.bg-gray-50');

  if (shortlistDiv) {
    const rect = shortlistDiv.getBoundingClientRect();
    if (
      jsEvent.clientX >= rect.left &&
      jsEvent.clientX <= rect.right &&
      jsEvent.clientY >= rect.top &&
      jsEvent.clientY <= rect.bottom
    ) {
      handleDropFromCalendar(event); 
    }
  }
}

// Customize calendar
const calendarOptions = ref<CalendarOptions>({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridThreeDays',
  headerToolbar: {
    left: 'prev',
    right: 'next'
  },
  allDaySlot: false,
  slotMinTime: '00:00',
  slotMaxTime: '24:00',
  height: 'auto',
  editable: true,
  slotLabelFormat: {
    hour: 'numeric',
    hour12: false
  },
  eventResizableFromStart: true,
  snapDuration: '00:10:00',
  visibleRange: currentDateRange.value,
  droppable: true,
  eventStartEditable: true,

  // Header: Day 1, Day 2, Day 3
  views: {
    timeGridThreeDays: {
      type: 'timeGrid',
      duration: { days: 3 },
      dayHeaderContent: (arg: any) => formatDayHeader(arg.date),
    }
  },

  events: [
    {
      id: '1',
      title: 'Museum of The Future',
      start: '2025-07-08T08:10:00',
      end: '2025-07-08T10:10:00',
    },
    {
      id: '2',
      title: 'Ninive',
      start: '2025-07-08T10:40:00',
      end: '2025-07-08T13:40:00',
    },
  ],

  // Render events
  eventContent: (arg: any) => {
    return {
      html: `
        <div class="p-2 bg-indigo-100 border-l-4 border-indigo-400 rounded w-full h-full text-gray-500 flex flex-col gap-y-1">
          <div class="font-medium text-gray-700">${arg.event.title}</div>
          <div class="text-xs">${arg.timeText}</div>
        </div>
      `
    };
  },

  eventReceive: (info) => handleEventReceive(info),

  eventDragStop: (info) => handleDragStop(info),
});

// Register shortlistItem as the external event source of FullCalendar
onMounted(() => {
  const shortlistEl = document.querySelector('.fc-draggable')?.parentElement;
  if (shortlistEl) {
    new Draggable(shortlistEl, {
      itemSelector: '.fc-draggable',
      eventData: function (el) {
        const data = el.dataset.transfer ? JSON.parse(el.dataset.transfer) : {};
        return {
          title: data.name,
          duration: { hours: data.duration || 2 },
          extendedProps: {
            ...data
          }
        };
      }
    });
  }
});
</script>

<style>
.fc .fc-daygrid-day-frame
.fc .fc-timegrid-slot {
  min-height: 2rem;
}

/* Header style */
.fc .fc-col-header-cell {
  padding-block: 0.5rem;
  text-align: center;
  font-weight: bold;
  color: var(--color-indigo-800);
}

/* Time slot style */
.fc .fc-timegrid-slot-label-cushion {
  font-size: 0.85rem;
  color: #6b7280;
  font-family: monospace;
}

.fc .fc-timegrid-slot-label {
  padding-right: 8px;
  padding-left: 8px;
}

/* Remove default today background */
.fc-timegrid-col {
  background-color: transparent !important;
}

/* Remove default event background */
.fc .fc-event {
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
}

.scroll-container {
  overflow: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

</style>