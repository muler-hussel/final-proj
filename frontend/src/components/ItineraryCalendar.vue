<template>
  <div class="fixed inset-0 z-50 p-1">
    <div class="flex relative w-full h-[calc(100vh-8px)] max-w-none transform overflow-hidden bg-white text-left shadow-xl transition-all rounded-xl">
      <!-- Close button -->
      <button 
        @click="onCancel"
        class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Calendar area -->
      <div class="w-7/10 p-1 mr-4 scroll-container">
        <FullCalendar ref="calendarRef" :options="calendarOptions" />
      </div>
      
      <!-- Discarded area -->
      <div class="flex flex-col w-3/10 p-4 h-full bg-gray-50 rounded-xl shadow-xl overflow-y-auto drop-container">
        <div class="text-xs text-gray-300 p-4">Drag event here, if you want to discard it</div>
        <div 
          v-for="(place, idx) in discardPlaces" 
          :key="idx"
          draggable="true"
          class="mb-2 p-3 cursor-move fc-draggable"
          :data-transfer="JSON.stringify(place)"
        >
          <SpotSelected v-if="placeDetails.get(place.name)" :item="placeDetails.get(place.name)!"></SpotSelected>
          <div v-else p-2 bg-indigo-100 border-l-4 border-indigo-400 rounded w-full h-full text-gray-500 flex flex-col gap-y-1>
            {{ place.name }}
          </div>
        </div>
        <div class="mt-auto px-4 py-3 sm:px-6 flex justify-end rounded-b-lg gap-3">
          <a-button @click="onCancel">Cancel</a-button>
          <a-button @click="saveItinerary" type="primary">Save</a-button>
        </div>
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
import { ref, onMounted, type PropType, computed, watch } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin, { Draggable, type EventReceiveArg, type EventDragStopArg} from '@fullcalendar/interaction';
import { type CalendarOptions, type EventApi, type EventClickArg, type EventContentArg, type EventInput } from '@fullcalendar/core';
import { useShortlistStore } from '@/stores/shortlist.ts';
import SpotSelected from '@/components/SpotSelected.vue';
import { storeToRefs } from 'pinia';
import type { DailyItinerary, ShortlistItem, DiscardPlace } from '@/types';
import dayjs from 'dayjs';
import { useItineraryStore } from '@/stores/itinerary';

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
const discardPlaces = ref<Set<DiscardPlace>>(new Set([]));
const useItinerary = useItineraryStore();

const saveItinerary = async () => {
  useItinerary.itineraryOpen= false;
  await useItinerary.handleSave();
}

const onCancel = async () => {
  if (useItinerary.ifChanged()) {
    const confirmLeave = window.confirm("Changes you made may not be saved. Do you want to leave this page?");
    if (confirmLeave) {
      useItinerary.clearChange();
    } else {
      useItinerary.itineraryOpen = true;
    }
  }
  useItinerary.clearChange();
}

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
    
    let title = undefined;
    let place_info = null;
    if (item.place_name) {
      title = item.place_name;
      place_info = items.value.get(title);
    }
    const eventTitle = title ? title : item.commute_mode;

    return {
      id: `event-${index}`,
      title: eventTitle ?? undefined,
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
      place_name: type === 'visit' ? event.title : null,
      start_time: start.format('HH:mm'),
      end_time: end.format('HH:mm'),
      commute_mode: type === 'commute' ? event.title : null,
      discarded_places: Array.from(discardPlaces.value),
    } satisfies DailyItinerary;
  });
}

// Customize Header as Day 1, Day 2, Day 3
const formatDayHeader = (date: Date) => {
  const startDate = Date.now();
  const diffDays = Math.floor((+date - +startDate) / (1000 * 60 * 60 * 24)) + 2;
  return `Day ${diffDays}`;
};

const setOperations = {
  add: (place: DiscardPlace) => {
    const newSet = new Set(discardPlaces.value);
    [...newSet].find(p => p.name === place.name) && newSet.delete([...newSet].find(p => p.name === place.name)!);
    discardPlaces.value = newSet.add(place);
  },
  delete: (name: string) => {
    const newSet = new Set(discardPlaces.value);
    [...newSet].find(p => p.name === name) && newSet.delete([...newSet].find(p => p.name === name)!);
    discardPlaces.value = new Set(newSet);
  }
};

// Calendar receive from discardPlaces
const handleEventReceive = (info: EventReceiveArg) => {
  console.log(info)
  if (!info.draggedEl.dataset.transfer) return;
  const place = JSON.parse(info.draggedEl.dataset.transfer);
  info.event.setProp('title', place.name);
  info.event.setExtendedProp('placeId', place.id);
  info.event.setExtendedProp('type', place.extendedProps.type);
  info.event.setExtendedProp('openingHours', place.extendedProps.openingHours);
  
  if (!info.event.start) return;
  const end = new Date(info.event.start);
  end.setHours(end.getHours() + place.duration);
  info.event.setEnd(end);
  setOperations.delete(place.name);
};

// DiscardPlaces receive from calendar
const handleDropFromCalendar = (event: EventApi) => {
  if(event.extendedProps.type === 'visit') {
    deleteEvent(event);
  }
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
      const place = {
        name: event.title,
        duration: (+event.end - +event.start) / 3600000,
        extendedProps:{
          openingHours: event.extendedProps.openingHours,
          type: event.extendedProps.type,
        }
      };
      setOperations.add(place);
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
    const title = arg.event.title;
    const icon = {
      'walking': '👣',
      'transit': '🚌',
      'bicycling': '🚲',
      'driving': '🚙',
    }[title.toLowerCase()] || '✈️';
    // Make sure drag mirror rendered in type visit way
    const isMirror = arg.isMirror
    const type = arg.event.extendedProps?.type || (isMirror ? 'visit' : 'commute')
    
    return {
      html: `
        ${type === 'visit' ?
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
        `<div class="m-auto bg-amber-100/50 rounded w-1/2 h-full border-dashed border-amber-200 border-1 text-gray-500 flex flex-row gap-x-1 items-center">
          <div>${icon}</div> 
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

let draggableInstance: Draggable | null = null
// Register shortlistItem as the external event source of FullCalendar
const initDraggable = () => {
  // Cannot get children els from class drop-container, can only get from the whole document.
  // Using watch to guarantee, only when discardPlaces changed, el register as Draggable.
  // Use draggableInstance to guarantee only one instance exsits.
  if (draggableInstance) draggableInstance.destroy();
  draggableInstance = new Draggable(document.body, {
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
};

watch(discardPlaces, () => {
  initDraggable();
}); 

onMounted(() => {
  // Something wrong with onMounted, mount for 3 times. If initDraggable() here, 3 instances exsits every time.
  // Due to parent components mount for several times.
  useItinerary.registerExtractFn(extractEventData);
  if (events.length > 0) {
    const firstEvent = events[0]
    const places = firstEvent.discarded_places || []
    discardPlaces.value.clear()
    places.forEach((place: DiscardPlace) => {
      discardPlaces.value.add(place)
    })
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
  background: #ffffff;
  color: #828282;
  text-align: start;
  border-radius: 4px;
  border-width: 1px;
  border-color: #a8a7a7;
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