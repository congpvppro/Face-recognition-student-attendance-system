import { db } from "@user/sqlite";
import { faceRecognitionGateway } from "../gateway";

export class UnregisteredFaceService {
  constructor() {
    this.initDatabase();
  }

  private initDatabase() {
    db.run(`
            CREATE TABLE IF NOT EXISTS unregistered_faces (
                face_id TEXT PRIMARY KEY,
                class_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes (id)
            );
        `);
  }

  public addUnregisteredFace(faceId: string, classId: number): void {
    const query = db.query(
      "INSERT INTO unregistered_faces (face_id, class_id, created_at) VALUES ($face_id, $class_id, $created_at)",
    );
    query.run({
      $face_id: faceId,
      $class_id: classId,
      $created_at: new Date().toISOString(),
    });
  }

  public getUnregisteredFaces(
    teacherId?: number,
  ): { face_id: string; class_id: number }[] {
    if (teacherId) {
      const query = db.query(`
	               SELECT uf.face_id, uf.class_id
	               FROM unregistered_faces uf
	               JOIN classes c ON uf.class_id = c.id
	               WHERE c.teacher_id = $teacherId
	           `);
      return query.all({ $teacherId: teacherId }) as {
        face_id: string;
        class_id: number;
      }[];
    }
    const query = db.query("SELECT face_id, class_id FROM unregistered_faces");
    return query.all() as { face_id: string; class_id: number }[];
  }

  public async deleteUnregisteredFace(faceId: string): Promise<void> {
    await faceRecognitionGateway.deleteUnregisteredFace(faceId);

    const query = db.query(
      "DELETE FROM unregistered_faces WHERE face_id = $face_id",
    );
    query.run({ $face_id: faceId });
  }
}
