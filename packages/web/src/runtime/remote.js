/**
 * Tier 1/2: talk to a `nishachar serve` backend.
 *
 * The backend decides whether that means the local toolchain or a container;
 * this side only speaks the JSON API.
 */

export class RemoteRuntime {
  constructor(endpoint) {
    this.endpoint = String(endpoint).replace(/\/+$/, '');
    this.id = 'remote';
  }

  get label() {
    return 'server';
  }

  async languages() {
    const response = await fetch(`${this.endpoint}/api/languages`);
    if (!response.ok) throw new Error(`server returned ${response.status}`);
    const body = await response.json();
    return body.languages;
  }

  async health() {
    const response = await fetch(`${this.endpoint}/api/health`);
    if (!response.ok) throw new Error(`server returned ${response.status}`);
    return response.json();
  }

  supports() {
    // The server has every language in the registry; it decides at run time
    // whether it can actually reach a toolchain for one.
    return true;
  }

  async run({ language, code, stdin = '', timeout, signal }) {
    const response = await fetch(`${this.endpoint}/api/run`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ language: language.id, code, stdin, timeout }),
      signal,
    });

    let body;
    try {
      body = await response.json();
    } catch {
      throw new Error(`server returned ${response.status} with a non-JSON body`);
    }
    if (!response.ok) throw new Error(body.error || `server returned ${response.status}`);
    return body;
  }
}
