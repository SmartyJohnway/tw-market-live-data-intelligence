'use strict';
// CI-only Node boundary. The state-contract test needs no sockets or children.
const fs = require('node:fs');
const log = process.env.TW_MARKET_CI_GUARD_LOG;
function emit(event, reason) {
  fs.appendFileSync(log, JSON.stringify({event, reason, pid: process.pid}) + '\n');
}
function deny() { emit('denied', 'NODE_NETWORK_OR_CHILD_ATTEMPT'); throw new Error('DETERMINISTIC_CI_NODE_DENIED'); }
const net = require('node:net');
net.Socket.prototype.connect = deny;
net.connect = deny; net.createConnection = deny;
for (const name of ['node:http', 'node:https', 'node:http2']) {
  const mod = require(name);
  for (const key of ['request', 'get', 'connect']) if (typeof mod[key] === 'function') mod[key] = deny;
}
for (const name of ['node:dns', 'node:dns/promises']) {
  const mod = require(name);
  for (const key of Object.keys(mod)) if (/^(lookup|resolve|reverse)/.test(key) && typeof mod[key] === 'function') mod[key] = deny;
}
const udp = require('node:dgram'); udp.createSocket = deny;
require('node:worker_threads').Worker = class { constructor() { deny(); } };
const children = require('node:child_process');
for (const key of Object.keys(children)) if (typeof children[key] === 'function') children[key] = deny;
globalThis.fetch = deny;
emit('guard_loaded_node', 'state_contract_only');
