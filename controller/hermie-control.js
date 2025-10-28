// hermie-control.js
(function (Scratch) {
  'use strict';

  class HermieControl {
    constructor() {
      this.baseURL = 'http://100.101.120.3:5000';
      this.deviceResponses = {};
      this.deviceErrors = {};
      this.sensorData = {};
      this.healthData = {};
    }

    // Helper: fetch with timeout
    async _fetch(url, options = {}) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.error || `HTTP ${res.status}`);
        }
        return await res.json();
      } finally {
        clearTimeout(timeout);
      }
    }

    getInfo() {
      return {
        id: 'hermiecontrol',
        name: 'Hermie Control',
        color1: '#FF6B35',
        color2: '#E85D31',
        blocks: [
          {
            opcode: 'setBaseURL',
            blockType: Scratch.BlockType.COMMAND,
            text: 'set base URL to [URL]',
            arguments: { URL: { type: Scratch.ArgumentType.STRING, defaultValue: this.baseURL } }
          },
          {
            opcode: 'setDevice',
            blockType: Scratch.BlockType.COMMAND,
            text: 'set [DEVICE] [STATE]',
            arguments: {
              DEVICE: { type: Scratch.ArgumentType.STRING, menu: 'devices', defaultValue: 'heat' },
              STATE: { type: Scratch.ArgumentType.STRING, menu: 'states', defaultValue: 'on' }
            }
          },
          {
            opcode: 'getDeviceField',
            blockType: Scratch.BlockType.REPORTER,
            text: '[DEVICE] response [FIELD]',
            arguments: {
              DEVICE: { type: Scratch.ArgumentType.STRING, menu: 'devices', defaultValue: 'heat' },
              FIELD: { type: Scratch.ArgumentType.STRING, menu: 'deviceFields', defaultValue: 'status' }
            }
          },
          {
            opcode: 'getDeviceError',
            blockType: Scratch.BlockType.REPORTER,
            text: '[DEVICE] last error',
            arguments: { DEVICE: { type: Scratch.ArgumentType.STRING, menu: 'devices', defaultValue: 'heat' } }
          },
          {
            opcode: 'isDeviceOn',
            blockType: Scratch.BlockType.BOOLEAN,
            text: '[DEVICE] is on?',
            arguments: { DEVICE: { type: Scratch.ArgumentType.STRING, menu: 'devices', defaultValue: 'heat' } }
          },
          {
            opcode: 'deviceAsJSON',
            blockType: Scratch.BlockType.REPORTER,
            text: '[DEVICE] response as JSON',
            arguments: { DEVICE: { type: Scratch.ArgumentType.STRING, menu: 'devices', defaultValue: 'heat' } }
          },
          '---',
          {
            opcode: 'fetchSensor',
            blockType: Scratch.BlockType.COMMAND,
            text: 'fetch sensor data'
          },
          {
            opcode: 'getSensorField',
            blockType: Scratch.BlockType.REPORTER,
            text: 'sensor [FIELD]',
            arguments: {
              FIELD: { type: Scratch.ArgumentType.STRING, menu: 'sensorFields', defaultValue: 'temperature_f' }
            }
          },
          {
            opcode: 'getSensorError',
            blockType: Scratch.BlockType.REPORTER,
            text: 'sensor error'
          },
          {
            opcode: 'isSensorReadOK',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'sensor read ok?'
          },
          {
            opcode: 'hasAlert',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'sensor has alert?'
          },
          {
            opcode: 'sensorAsJSON',
            blockType: Scratch.BlockType.REPORTER,
            text: 'sensor data as JSON'
          },
          '---',
          {
            opcode: 'checkHealth',
            blockType: Scratch.BlockType.COMMAND,
            text: 'check system health'
          },
          {
            opcode: 'getHealthStatus',
            blockType: Scratch.BlockType.REPORTER,
            text: 'health status'
          },
          {
            opcode: 'isHealthy',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'system is healthy?'
          }
        ],
        menus: {
          devices: { acceptReporters: true, items: ['heat', 'pump'] },
          states: { acceptReporters: true, items: ['on', 'off'] },
          deviceFields: { acceptReporters: true, items: ['status', 'timestamp'] },
          sensorFields: {
            acceptReporters: true,
            items: ['temperature_f', 'temperature_c', 'humidity', 'alert', 'error',
                   'timestamp_iso', 'heat_on', 'pump_on']
          }
        }
      };
    }

    setBaseURL(args) {
      const url = args.URL.trim();
      if (url) this.baseURL = url.replace(/\/$/, '');
    }

    async setDevice(args) {
      const device = args.DEVICE;
      try {
        const json = await this._fetch(`${this.baseURL}/control/${device}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ state: args.STATE.toLowerCase() }),
          cache: 'no-store'
        });
        this.deviceResponses[device] = json;
        this.deviceErrors[device] = null;
      } catch (e) {
        this.deviceErrors[device] = e.message;
        this.deviceResponses[device] = null;
      }
    }

    getDeviceField(args) {
      const response = this.deviceResponses[args.DEVICE];
      if (!response) return '';
      const val = response[args.FIELD];
      return val ?? '';
    }

    getDeviceError(args) {
      return this.deviceErrors[args.DEVICE] || '';
    }

    isDeviceOn(args) {
      const device = args.DEVICE;
      const response = this.deviceResponses[device];
      const key = `${device}_on`;

      // Check control response first, fall back to sensor data
      if (response && key in response) return Boolean(response[key]);
      if (key in this.sensorData) return Boolean(this.sensorData[key]);
      return false;
    }

    deviceAsJSON(args) {
      const response = this.deviceResponses[args.DEVICE];
      return response ? JSON.stringify(response) : '{}';
    }

    async fetchSensor() {
      try {
        const json = await this._fetch(`${this.baseURL}/sensor?_=${Date.now()}`, { cache: 'no-store' });
        this.sensorData = json;
      } catch (e) {
        this.sensorData = { error: e.message, last_read_ok: false };
      }
    }

    getSensorField(args) {
      const val = this.sensorData[args.FIELD];
      return val ?? '';
    }

    getSensorError() {
      return this.sensorData.error || '';
    }

    isSensorReadOK() {
      return Boolean(this.sensorData.last_read_ok);
    }

    hasAlert() {
      return Boolean(this.sensorData.alert);
    }

    sensorAsJSON() {
      return JSON.stringify(this.sensorData);
    }

    async checkHealth() {
      try {
        this.healthData = await this._fetch(`${this.baseURL}/health`, { cache: 'no-store' });
      } catch (e) {
        this.healthData = { status: 'error', error: e.message };
      }
    }

    getHealthStatus() {
      return this.healthData.status || '';
    }

    isHealthy() {
      return this.healthData.status === 'ok';
    }
  }

  Scratch.extensions.register(new HermieControl());
})(Scratch);
