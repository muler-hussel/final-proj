<template>
  <a-drawer title="Your Shortlist" 
    :open="drawer.shortlists.isOpen" 
    @close="drawer.onShortlistsClose()" 
    class="flex flex-col" width="500"
    @afterOpenChange="onDrawerOpenChange"
  >
    <div class="flex-1 scroll-container mb-2 min-h-0 h-[calc(100vh-420px)]">
      <div class="grid gap-2">
        <SpotSelected
          v-for="item in Array.from(items.values())" 
          :key="item.name"
          :item="item"
          :ref="el => setSpotRef(el, item.name)"
        ></SpotSelected>
      </div>
    </div>
    <div id="mapContainer" class="h-[300px] rounded-2xl"></div>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, computed, nextTick, watch, onUnmounted } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import { useShortlistStore } from '@/stores/shortlist.ts';
import SpotSelected from './SpotSelected.vue';

export default defineComponent({
  components: { SpotSelected },
  setup() {
    const drawer = useDrawerStore();
    const shortlistStore = useShortlistStore();
    const items = computed(() => Array.from(shortlistStore.items.values()))
    let map: google.maps.Map | null = null
    let markers: google.maps.marker.AdvancedMarkerElement[] = []
    const spotRefs = new Map<string, HTMLElement>()

    const markerElement = document.createElement("div");
    markerElement.innerHTML = `
      <div style="
        background: #9370DB;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid white;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
      ">1</div>
    `;

    const clearMapResources = () => {
      markers.forEach(marker => {
        google.maps.event.clearInstanceListeners(marker);
        marker.map = null;
      });
      markers = [];
    }

    const loadMapAPI = async() => {
      return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_API}&libraries=marker&loading=async`;
        script.onload = resolve;
        script.onerror = () => {
          reject(new Error('Failed to load Google Maps'));
        };
        document.head.appendChild(script);
      });
    }

    const initMap = async() => {
      try {
        if (!window.google?.maps?.Map) await loadMapAPI();
        
        const mapContainer = document.getElementById('mapContainer');
        if (!mapContainer) throw new Error("Fail to find mapContainer");
        
        map = new google.maps.Map(mapContainer, {
          center: { lat: 39.9042, lng: 116.4074 },
          zoom: 12,
          mapId: "DEMO_MAP_ID",
        });
        
        updateMarkers();
      } catch (err) {
        console.error('Map init failed:', err);
      }
    }

    const updateMarkers = () => {
      clearMapResources();
      
      items.value.forEach((item, index) => {
        if (!item.geometry?.location || !map) return;
        
        const markerEl = markerElement.cloneNode(true) as HTMLElement;
        markerEl.querySelector('div')!.textContent = `${index + 1}`;
        
        const marker = new google.maps.marker.AdvancedMarkerElement({
          position: {
            lat: item.geometry.location[0],
            lng: item.geometry.location[1]
          },
          map,
          title: item.name,
          content: markerEl,
        });
        
        marker.addListener("click", () => scrollToSpot(item.name));
        
        markers.push(marker);
      });
      
      fitMapToMarkers();
    }

    const fitMapToMarkers = () => {
      if (!map || markers.length === 0) return;
      
      const bounds = new google.maps.LatLngBounds();
      markers.forEach(marker => {
        if (marker.position) bounds.extend(marker.position);
      });
      
      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, 50);
      }
    }

    const onDrawerOpenChange = async() => {
      await nextTick();
      if (!map) initMap();
    }

    const setSpotRef = (el: any, name: string) => {
      if (el?.$el) {
        spotRefs.set(name, el.$el);
      } else if (el instanceof HTMLElement) {
        spotRefs.set(name, el);
      }
    }

    const scrollToSpot = (name: string) => {
      const el = spotRefs.get(name);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });

        el.classList.add('border-2', 'border-violet-400');
        setTimeout(() => {
          el.classList.remove('border-2', 'border-violet-400');
        }, 1500);
      }
    }

    watch(items, updateMarkers, { deep: true });
    
    onUnmounted(() => clearMapResources());

    return {
      drawer,
      SpotSelected,
      shortlistStore,
      items,
      onDrawerOpenChange,
      setSpotRef,
    }
  }
})
</script>

<style scoped>
.scroll-container {
  overflow: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}
</style>