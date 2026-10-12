import { AfterViewInit, Component, ElementRef, OnDestroy, effect, input, viewChild } from '@angular/core';
import * as L from 'leaflet';

import { PuntoMapa } from '../../../core/services/dashboard.service';

const CENTRO_LATAM: L.LatLngExpression = [-15, -60];
const ZOOM_INICIAL = 3;

@Component({
  selector: 'app-mapa-riesgo',
  imports: [],
  templateUrl: './mapa-riesgo.html',
  styleUrl: './mapa-riesgo.scss',
})
export class MapaRiesgo implements AfterViewInit, OnDestroy {
  readonly puntos = input<PuntoMapa[]>([]);

  private readonly contenedor = viewChild.required<ElementRef<HTMLDivElement>>('mapaEl');
  private mapa: L.Map | null = null;
  private marcadores: L.CircleMarker[] = [];
  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    effect(() => {
      this.dibujarMarcadores(this.puntos());
    });
  }

  ngAfterViewInit(): void {
    const elemento = this.contenedor().nativeElement;
    this.mapa = L.map(elemento, { scrollWheelZoom: false }).setView(CENTRO_LATAM, ZOOM_INICIAL);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18,
    }).addTo(this.mapa);

    // El contenedor puede no tener aun su tamano final cuando se crea el mapa (p. ej.
    // dentro de un mat-card que todavia esta maquetando el layout de dos columnas), lo
    // que deja zonas grises hasta el primer resize manual. ResizeObserver dispara al
    // observar por primera vez y cada vez que el tamano real cambia despues.
    this.resizeObserver = new ResizeObserver(() => {
      this.mapa?.invalidateSize();
      this.ajustarVista();
    });
    this.resizeObserver.observe(elemento);

    this.dibujarMarcadores(this.puntos());
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.mapa?.remove();
  }

  private dibujarMarcadores(puntos: PuntoMapa[]): void {
    if (!this.mapa) {
      return;
    }

    for (const marcador of this.marcadores) {
      marcador.remove();
    }
    this.marcadores = puntos.map((punto) =>
      L.circleMarker([punto.latitud, punto.longitud], {
        radius: 12,
        color: '#ffffff',
        weight: 1.5,
        fillColor: punto.color,
        fillOpacity: 0.9,
      })
        .bindTooltip(`${punto.nombre}<br>IRPC: ${punto.indice_compuesto} (${punto.nivel_riesgo})`)
        .addTo(this.mapa!),
    );

    this.ajustarVista();
  }

  private ajustarVista(): void {
    if (!this.mapa || this.marcadores.length === 0) {
      return;
    }
    const limites = L.latLngBounds(this.marcadores.map((marcador) => marcador.getLatLng()));
    this.mapa.fitBounds(limites, { padding: [24, 24] });
  }
}
