import { PYTHON_API_URL } from "@common/config";

interface RecognitionResult {
  student_id: string;
  similarity: number;
}

interface FaceRegistrationResult {
  face_id: string;
  message: string;
  class_id: number;
}

interface FaceCommitResult {
  message: string;
}

interface FaceDeleteResult {
  message: string;
}

/**
 * Extract error detail from response
 */
async function extractErrorDetail(
  response: Response,
  defaultMessage: string,
): Promise<string> {
  try {
    const error = (await response.json()) as { detail?: string };
    return error.detail || defaultMessage;
  } catch {
    return defaultMessage;
  }
}

/**
 * Gateway for communicating with the Python Face Recognition API
 */
export const faceRecognitionGateway = {
  /**
   * Recognize a face in an image
   */
  recognize: async (image: Blob): Promise<RecognitionResult> => {
    const formData = new FormData();
    formData.append("file", image, "image.jpg");

    const response = await fetch(`${PYTHON_API_URL}/recognize`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const detail = await extractErrorDetail(
        response,
        "Face recognition failed",
      );
      throw new Error(detail);
    }

    return response.json() as Promise<RecognitionResult>;
  },

  /**
   * Register a new face for later assignment to a student
   */
  registerFace: async (
    image: Blob,
    classId: number,
  ): Promise<FaceRegistrationResult> => {
    const formData = new FormData();
    formData.append("file", image, "image.jpg");
    formData.append("class_id", String(classId));

    const response = await fetch(`${PYTHON_API_URL}/register_face`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const detail = await extractErrorDetail(
        response,
        "Face registration failed",
      );
      throw new Error(detail);
    }

    return response.json() as Promise<FaceRegistrationResult>;
  },

  /**
   * Commit a registered face to a student ID
   */
  commitFace: async (
    studentId: string,
    faceId: string,
  ): Promise<FaceCommitResult> => {
    const formData = new FormData();
    formData.append("student_id", studentId);
    formData.append("face_id", faceId);

    const response = await fetch(`${PYTHON_API_URL}/commit_face`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const detail = await extractErrorDetail(response, "Face commit failed");
      throw new Error(detail);
    }

    return response.json() as Promise<FaceCommitResult>;
  },

  /**
   * Delete all face embeddings for a student
   */
  deleteFace: async (studentId: string): Promise<FaceDeleteResult> => {
    const response = await fetch(`${PYTHON_API_URL}/delete_face/${studentId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const detail = await extractErrorDetail(response, "Face deletion failed");
      throw new Error(detail);
    }

    return response.json() as Promise<FaceDeleteResult>;
  },

  /**
   * Delete an unregistered face by its temporary ID
   */
  deleteUnregisteredFace: async (faceId: string): Promise<FaceDeleteResult> => {
    const response = await fetch(
      `${PYTHON_API_URL}/unregister_face/${faceId}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      const detail = await extractErrorDetail(
        response,
        "Unregistered face deletion failed",
      );
      throw new Error(detail);
    }

    return response.json() as Promise<FaceDeleteResult>;
  },
};
