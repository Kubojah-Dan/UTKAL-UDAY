import Dexie from "dexie";

export const db = new Dexie("UtkalUdayDB");

// Schema:
// questions: key id, stores question objects
// interactions: key id (uuid), stores student interaction data for sync
db.version(1).stores({
    questions: "id, subject, grade, topic, type",
    interactions: "id, quest_id, student_id, synced, timestamp",
});

export const getLocalQuestions = async (params = {}) => {
    let collection = db.questions;
    if (params.subject) collection = collection.where("subject").equals(params.subject);
    if (params.grade) {
        const grade = Number(params.grade);
        if (params.subject) {
            collection = collection.filter(q => q.grade === grade);
        } else {
            collection = collection.where("grade").equals(grade);
        }
    }
    return collection.toArray();
};

export const saveQuestionsLocally = async (questions) => {
    return db.questions.bulkPut(questions);
};

export const queueInteraction = async (interaction) => {
    return db.interactions.add({
        ...interaction,
        id: crypto.randomUUID(),
        synced: 0,
        timestamp: Date.now(),
    });
};

export const getUnsyncedInteractions = async () => {
    return db.interactions.where("synced").equals(0).toArray();
};

export const markInteractionsSynced = async (ids) => {
    return db.interactions.where("id").anyOf(ids).modify({ synced: 1 });
};
