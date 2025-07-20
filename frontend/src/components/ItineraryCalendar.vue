<template>
  <div class="flex h-[calc(100vh-70px)]">
    <div class="w-7/10 mr-4 scroll-container">
      <FullCalendar
        ref="calendarRef"
        :options="calendarOptions"
      />
    </div>
    <div class="w-3/10 p-4 bg-gray-50 rounded-xl shadow-xl overflow-y-auto drop-container">
      <div class="text-xs text-gray-300 p-4">Drag event here, if you want to discard it</div>
      <div 
        v-for="place in discardPlaces" 
        :key="place.id"
        draggable="true"
        @dragstart="handleDragStart($event, place)"
        class="mb-2 p-3 cursor-move fc-draggable"
        :data-transfer="JSON.stringify(place)"
      >
        <SpotSelected v-if="placeDetails.get(place.name)" :item="placeDetails.get(place.name)!"></SpotSelected>
      </div>
    </div>
  </div>
  <a-modal v-model:open="open" centered>
    <template #footer>
      <a-button key="copy" @click="handleCopy">Copy</a-button>
      <a-button key="delete" type="primary" @click="handleDelete">Delete</a-button>
    </template>
    <p><strong class="text-violet-500">Title: </strong>{{ currentEvent?.title }}</p>
    <p v-if="currentEvent?.start && currentEvent.end" class="mt-1"> 
      <ClockCircleOutlined class="mr-5" style="color:#9370DB;"/>
      {{ formatTime(currentEvent?.start) }} - {{ formatTime(currentEvent?.end) }}
    </p>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, onMounted, type PropType, computed, nextTick } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin, { Draggable, type EventReceiveArg, type EventDragStopArg} from '@fullcalendar/interaction';
import { type CalendarOptions, type EventApi, type EventClickArg, type EventContentArg, type EventInput } from '@fullcalendar/core';
import { useShortlistStore } from '@/stores/shortlist.ts';
import SpotSelected from '@/components/SpotSelected.vue';
import { storeToRefs } from 'pinia';
import type { DailyItinerary, ShortlistItem } from '@/types';
import dayjs from 'dayjs';

interface Place {
  id: string;
  name: string;
  duration: number; //Hours
}

const {events, recommends} = defineProps({
  events: {
    type: Array as PropType<DailyItinerary[]>,
    default: () => []
  },
  recommends: {
    type: Array as PropType<ShortlistItem[]>,
    default: () => [],
  }
});
const calendarRef = ref();
const shortlistStore = useShortlistStore();
const { items } = storeToRefs(shortlistStore);
const placeDetails = computed(() => {
  const map = new Map<string, ShortlistItem>();
  recommends.forEach(item => map.set(item.name, item));
  for (const item of items.value.values()) {
    map.set(item.name, item);
  }
  return map;
});

// Convert DailyItinerary into EventInput
const convertToEventInput = (itineraries: DailyItinerary[]): EventInput[] => {
  return itineraries.map((item, index) => {
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + item.date - 1);
    
    const [startHours, startMinutes] = item.start_time.split(':').map(Number);
    const [endHours, endMinutes] = item.end_time.split(':').map(Number);
    const startTime = new Date(targetDate);
    startTime.setHours(startHours, startMinutes, 0, 0);
    const endTime = new Date(targetDate);
    endTime.setHours(endHours, endMinutes, 0, 0);
    
    let title = null;
    let place_info = null;
    if (item.place_name) {
      title = item.place_name;
      place_info = items.value.get(title);
    }

    return {
      id: `event-${index}`,
      title: title ? title : item.commute_mode,
      start: startTime,
      end: endTime,
      extendedProps: {
        openingHours: place_info?.info?.weekday_text,
        type: item.type,
      }
    };
  });
};

const calendarEvents = computed(() => {
  return convertToEventInput(events);
});

// Extract EventInput as DailyItinerary
const extractEventData = () => {
  const events: EventApi[] = calendarRef.value.getApi().getEvents();
  const baseDate = dayjs(events[0]?.start || new Date()).startOf('day');
  return events.map(event => {
    const start = dayjs(event.start);
    const end = dayjs(event.end);
    const type = event.extendedProps.type;

    return {
      date: start.diff(baseDate, 'day') + 1,
      type,
      place_name: type === 'visit' ? event.title : undefined,
      start_time: start.format('HH:mm'),
      end_time: end.format('HH:mm'),
      commute_mode: type === 'commuting' ? event.title : undefined,
    } satisfies DailyItinerary;
  });
}


// Customize Header as Day 1, Day 2, Day 3
const formatDayHeader = (date: Date) => {
  const startDate = Date.now();
  const diffDays = Math.floor((+date - +startDate) / (1000 * 60 * 60 * 24)) + 2;
  return `Day ${diffDays}`;
};

const discardPlaces = ref<Set<Place>>(new Set([]));

const setOperations = {
  add: (place: Place) => {
    discardPlaces.value = new Set([...discardPlaces.value, place]);
  },
  delete: (id: string) => {
    const newSet = new Set(discardPlaces.value);
    [...newSet].find(p => p.id === id) && newSet.delete([...newSet].find(p => p.id === id)!);
    discardPlaces.value = new Set(newSet);
  }
};

// Drag from discardPlaces to calendar
const handleDragStart = (e: DragEvent, place: Place) => {
  if (!e.dataTransfer) return;
  e.dataTransfer.setData('text/plain', JSON.stringify(place));
};

// Calendar receive from discardPlaces
const handleEventReceive = (info: EventReceiveArg) => {
  if (!info.draggedEl.dataset.transfer) return;
  const place = JSON.parse(info.draggedEl.dataset.transfer);
  info.event.setProp('title', place.name);
  info.event.setExtendedProp('placeId', place.id);
  
  if (!info.event.start) return;
  const end = new Date(info.event.start);
  end.setHours(end.getHours() + place.duration);
  info.event.setEnd(end);
  
  setOperations.delete(place.id);
};

// DiscardPlaces receive from calendar
const handleDropFromCalendar = (event: EventApi) => {
  deleteEvent(event);
};

// Handle with drags stopping inside of discardPlaces area
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

// Click event, copy or delete
const open = ref<boolean>(false);
const currentEvent = ref<EventApi | null>(null);
const handleEventClick = (info: EventClickArg) => {
  const event = info.event;
  currentEvent.value = event;
  showModal();
};

const showModal = () => {
  open.value = true;
};

const handleCopy = () => {
  if (!currentEvent.value) return;

  const calendarApi = calendarRef.value.getApi();
  const originalEvent = currentEvent.value;

  calendarApi.addEvent({
    ...originalEvent.toPlainObject(),
    id: `copy_${Date.now()}`,
    title: `${originalEvent.title}`,
    start: originalEvent.start,
    end: originalEvent.end
  });

  open.value = false;
};

const handleDelete = () => {
  if (currentEvent.value) {
    deleteEvent(currentEvent.value);
  }
  open.value = false;
};

const formatTime = (date: Date | null) => {
  if (!date) return '--:--';
  
  return date.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false
  });
};

const deleteEvent = (event: EventApi) => {
  if (event && event.end && event.start) {
    if (event.extendedProps.type === 'visit') {
      setOperations.add({
        id: event.id,
        name: event.title,
        duration: (+event.end - +event.start) / 3600000
      });
    }
    event.remove();
  }
}

// Customize calendar
const calendarOptions = ref<CalendarOptions>({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridThreeDays',
  initialDate: new Date(),
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
  validRange: { start: new Date() },
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

  events: calendarEvents.value,

  // Render events
  eventContent: (arg: EventContentArg) => {
    const openingHours = arg.event.extendedProps.openingHours || [];
    const hasOpeningHours = openingHours.length > 0;
    return {
      html: `
        ${arg.event.extendedProps.type === 'visit' ?
        `<div class="p-2 bg-indigo-100 border-l-4 border-indigo-400 rounded w-full h-full text-gray-500 flex flex-col gap-y-1">
          <div class="font-medium text-gray-700">${arg.event.title}</div>
          <div class="text-xs">
            ${arg.timeText}
            ${hasOpeningHours ? `
            <span class="icon-tooltip ml-1">🛈
              <span class="tooltip-text">
                ${openingHours.map((hours: any) => `
                  <div>${hours}</div>
                `).join('')}
              </span>
            </span>
          ` : ''}
          </div>
        </div>` : 
        `<div class="p-2 bg-indigo-100 border-l-4 border-indigo-400 rounded w-full h-full text-gray-500 flex flex-col gap-y-1">
          <div class="font-medium text-gray-700">${arg.event.title}</div>
          <div class="text-xs">
            ${arg.timeText}
          </div>
        </div>`}
      `
    };
  },

  eventReceive: (info) => {handleEventReceive(info)},

  eventDragStop: (info) => handleDragStop(info),

  eventClick: (info) => handleEventClick(info),
});

// Register shortlistItem as the external event source of FullCalendar
const initDraggable = () => {
  const dropContainer = document.querySelector('.drop-container') as HTMLElement;
  if (dropContainer) {
    new Draggable(dropContainer, {
      itemSelector: '.fc-draggable',
      eventData: (el) => {
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
};

onMounted(() => {
  nextTick(() => {
    setTimeout(initDraggable, 100);
  });
});

defineExpose({ extractEventData });
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
  color: #8080ff;
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

/* Previous Next button */
.fc .fc-toolbar .fc-prev-button,
.fc .fc-toolbar .fc-next-button {
  background-color: white;
  color:#b47fff;
  border-color: transparent;
}

.fc .fc-prev-button:focus,
.fc .fc-next-button:focus,
.fc .fc-prev-button:active,
.fc .fc-next-button:active,
.fc .fc-prev-button:hover,
.fc .fc-next-button:hover {
  outline: none !important;
  box-shadow: none !important;
  color:#b47fff;
  border: 0;
  background-color: inherit !important;
}

.icon-tooltip {
  position: relative;
  cursor: pointer;
}

.tooltip-text {
  visibility: hidden;
  width: 205px;
  background: #c7c7c7;
  color: #ffffff;
  text-align: start;
  border-radius: 4px;
  padding: 4px;
  position: absolute;
  z-index: 100;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.icon-tooltip:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}

</style>