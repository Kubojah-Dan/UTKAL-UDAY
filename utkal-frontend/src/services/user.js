import { db } from "./pouch";
import { v4 as uuidv4 } from "uuid";

export async function ensureStudentId() {
    try {
        const doc = await db.get("meta:student");
        return doc.data.student_id;
    } catch (e) {
        const id = uuidv4();
        await db.put({ _id: "meta:student", data: { student_id: id } });
        return id;
    }
}
