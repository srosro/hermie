// sensor-oneshot.js
(function (Scratch) {
  'use strict';
  const BlockType = Scratch.BlockType;
  const ArgumentType = Scratch.ArgumentType;

  class OneShotSensor {
    constructor() {
      this.url = 'http://100.101.120.3:5000/sensor';
      this.data = {
        alert: null,
        error: null,
        humidity: null,
        last_read_ok: null,
        temperature_c: null,
        temperature_f: null,
        timestamp_iso: null
      };
    }

    getInfo() {
      return {
        id: 'oneshotsensor',
        name: 'One-Shot Sensor',
        color1: '#2E8B57',
        blocks: [
          {
            opcode: 'setURL',
            blockType: BlockType.COMMAND,
            text: 'set URL to [URL]',
            arguments: { URL: { type: ArgumentType.STRING, defaultValue: this.url } }
          },
          {
            opcode: 'fetchNow',
            blockType: BlockType.COMMAND,
            text: 'fetch from URL now'
          },
          {
            opcode: 'field',
            blockType: BlockType.REPORTER,
            text: 'sensor [FIELD]',
            arguments: {
              FIELD: {
                type: ArgumentType.STRING,
                menu: 'fields',
                defaultValue: 'temperature_f'
              }
            }
          },
          {
            opcode: 'asJSON',
            blockType: BlockType.REPORTER,
            text: 'sensor as JSON'
          }
        ],
        menus: {
          fields: {
            acceptReporters: true,
            items: [
              'temperature_f',
              'temperature_c',
              'humidity',
              'last_read_ok',
              'alert',
              'error',
              'timestamp_iso'
            ]
          }
        }
      };
    }

    setURL(args) {
      const u = String(args.URL || '').trim();
      if (u) this.url = u;
    }

    async fetchNow() {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const sep = this.url.includes('?') ? '&' : '?';
        const res = await fetch(`${this.url}${sep}_=${Date.now()}`, {
          cache: 'no-store',
          signal: controller.signal
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();

        this.data.alert = json.alert ?? null;
        this.data.error = json.error ?? null;
        this.data.humidity = Number(json.humidity ?? null);
        this.data.last_read_ok = Boolean(json.last_read_ok);
        this.data.temperature_c = Number(json.temperature_c ?? null);
        this.data.temperature_f = Number(json.temperature_f ?? null);
        this.data.timestamp_iso = String(json.timestamp_iso ?? null);
      } catch (e) {
        this.data.error = String(e && e.message ? e.message : e);
        this.data.last_read_ok = false;
      } finally {
        clearTimeout(timeout);
      }
    }

    field(args) {
      const key = String(args.FIELD || '');
      const v = Object.prototype.hasOwnProperty.call(this.data, key) ? this.data[key] : null;
      if (typeof v === 'number' || typeof v === 'boolean') return v;
      return v == null ? '' : String(v);
    }

    asJSON() {
      return JSON.stringify(this.data);
    }
  }

  Scratch.extensions.register(new OneShotSensor());
})(Scratch);
