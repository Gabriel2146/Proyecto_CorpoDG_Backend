import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api';

const destinosTrend = new Trend('destinos');
const paquetesTrend = new Trend('paquetes');
const vuelosTrend = new Trend('vuelos_live');

export const options = {
  stages: [
    { duration: '10s', target: 5 },
    { duration: '20s', target: 20 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    destinos: ['p(95)<3000'],
    paquetes: ['p(95)<3000'],
    vuelos_live: ['p(95)<30000'],
  },
};

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  let res = http.get(`${BASE_URL}/destinos/`, { headers });
  check(res, { 'destinos status 200': (r) => r.status === 200 });
  destinosTrend.add(res.timings.duration);

  res = http.get(`${BASE_URL}/paquetes/`, { headers });
  check(res, { 'paquetes status 200': (r) => r.status === 200 });
  paquetesTrend.add(res.timings.duration);

  const payload = JSON.stringify({
    origin: 'UIO',
    destination: 'GYE',
    date: '2026-08-15',
  });
  res = http.post(`${BASE_URL}/buscar-vuelos-live/`, payload, { headers });
  vuelosTrend.add(res.timings.duration);

  sleep(1);
}
