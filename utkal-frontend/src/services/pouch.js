import PouchDB from "pouchdb-core";
import PouchDBAdapterIdb from "pouchdb-adapter-idb";

// Register IndexedDB adapter
PouchDB.plugin(PouchDBAdapterIdb);

export const DB_NAME = "utkal_local";

// Create DB immediately (no lazy init needed)
export const db = new PouchDB(DB_NAME, {
  adapter: "idb",
});

// ---------- Quest → Skill ----------

export async function saveQuest2Skill(map) {
  const id = "meta:quest2skill";

  try {
    const doc = await db.get(id);
    return db.put({
      ...doc,
      data: map,
      _id: id,
    });
  } catch (e) {
    if (e.status === 404) {
      return db.put({
        _id: id,
        data: map,
      });
    }
    throw e;
  }
}

export async function getQuest2Skill() {
  try {
    const doc = await db.get("meta:quest2skill");
    return doc.data;
  } catch {
    return null;
  }
}

// ---------- BKT Params ----------

export async function saveBktParams(params) {
  const id = "meta:bkt_params";

  try {
    const doc = await db.get(id);
    return db.put({
      ...doc,
      data: params,
      _id: id,
    });
  } catch (e) {
    if (e.status === 404) {
      return db.put({
        _id: id,
        data: params,
      });
    }
    throw e;
  }
}

export async function getBktParams() {
  try {
    const doc = await db.get("meta:bkt_params");
    return doc.data;
  } catch {
    return null;
  }
}
