// Run with: node tests/test_activity_refresh.js
const { readFileSync } = require("node:fs");
const source = readFileSync("src/static/app.js", "utf8");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

class Element {
  constructor() {
    this.children = [];
    this.options = this.children;
    this.value = "";
    this.classList = { add() {}, remove() {} };
  }
  set innerHTML(value) {
    this.html = value;
    this.children.length = 0;
  }
  appendChild(child) { this.children.push(child); }
  setAttribute() {}
  addEventListener(event, callback) { this[event] = callback; }
  reset() {}
}

async function checkRefresh(staleRequestFails) {
  const elements = {};
  for (const id of ["activities-list", "activity", "signup-form", "email", "message"]) {
    elements[id] = new Element();
  }
  elements.activity.appendChild(new Element());
  elements.activity.value = "Chess Club";
  elements.email.value = "new@school.edu";
  const document = {
    getElementById: (id) => elements[id],
    createElement: () => new Element(),
    addEventListener: (event, callback) => callback(),
  };
  const activityData = (participants) => ({
    "Chess Club": {
      description: "Chess",
      schedule: "Friday",
      max_participants: 12,
      participants,
    },
  });
  let releaseStaleRequest;
  let rejectStaleRequest;
  const staleRequest = new Promise((resolve, reject) => {
    releaseStaleRequest = resolve;
    rejectStaleRequest = reject;
  });
  let loads = 0;
  const errors = [];
  const fetch = async (url, options) => {
    if (options) {
      assert(options.method === "POST", "Signup must use POST");
      return { ok: true, json: async () => ({ message: "Signed up" }) };
    }
    if (++loads === 1) return staleRequest;
    return {
      ok: true,
      json: async () => activityData(["existing@school.edu", "new@school.edu"]),
    };
  };
  new Function("document", "fetch", "console", "setTimeout", source)(
    document, fetch, { error: (...args) => errors.push(args) }, () => {}
  );
  await elements["signup-form"].submit({ preventDefault() {} });
  assert(loads === 2, "Successful signup must fetch updated activities");
  if (staleRequestFails) {
    rejectStaleRequest(new Error("Old request failed"));
  } else {
    releaseStaleRequest({
      ok: true,
      json: async () => activityData(["existing@school.edu"]),
    });
  }
  // Drain the earlier request's fetch, JSON parsing, and rendering continuations.
  for (let i = 0; i < 10; i++) await Promise.resolve();
  const card = elements["activities-list"].children[0];
  assert(card, "A stale failure must not clear current cards");
  const section = card.children[0];
  assert(section.children[0].textContent === "Participants (2)", "Count must stay current");
  const rows = section.children[1].children;
  assert(rows[1].children[0].textContent === "new@school.edu", "New participant must stay visible");
  assert(card.html.includes("10 spots left"), "Availability must stay current");
  assert(elements.activity.options.length === 2, "Dropdown options must not duplicate");
  assert(errors.length === Number(staleRequestFails), "Failures must be logged");
}

checkRefresh(false)
  .then(() => checkRefresh(true))
  .then(() => console.log("PASS: signup refresh and stale success/failure responses"))
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
