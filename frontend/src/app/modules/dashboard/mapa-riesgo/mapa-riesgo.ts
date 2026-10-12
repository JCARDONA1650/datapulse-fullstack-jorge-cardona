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

  constructor() {
    effect(() => {
      this.dibujarMarcadores(this.puntos());
    });
  }

  ngAfterViewInit(): void {
    this.mapa = L.map(this.contenedor().nativeElement, { scrollWheelZoom: false }).setView(CENTRO_LATAM, ZOOM_INICIAL);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18,
    }).addTo(this.mapa);
    this.dibujarMarcadores(this.puntos());
  }

  ngOnDestroy(): void {
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
  }
}
