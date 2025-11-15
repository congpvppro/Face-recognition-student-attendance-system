const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";

export const faceRecognitionGateway = {
	recognize: async (image: Blob) => {
		const formData = new FormData();
		formData.append("file", image, "image.jpg");

		const response = await fetch(`${PYTHON_API_URL}/recognize`, {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: "Face recognition failed" }));
			throw new Error(error.detail);
		}
		return response.json();
	},
	registerFace: async (image: Blob, classId: number) => {
		const formData = new FormData();
		formData.append("file", image, "image.jpg");
		formData.append("class_id", String(classId));

		const response = await fetch(`${PYTHON_API_URL}/register_face`, {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: "Face registration failed" }));
			throw new Error(error.detail);
		}
		return response.json();
	},
	commitFace: async (studentId: string, faceId: string) => {
		const formData = new FormData();
		formData.append("student_id", studentId);
		formData.append("face_id", faceId);

		const response = await fetch(`${PYTHON_API_URL}/commit_face`, {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: "Face commit failed" }));
			throw new Error(error.detail);
		}
		return response.json();
	},
	deleteFace: async (studentId: string) => {
		const response = await fetch(`${PYTHON_API_URL}/delete_face/${studentId}`, {
			method: "DELETE",
		});

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: "Face deletion failed" }));
			throw new Error(error.detail);
		}
		return response.json();
	},
	deleteUnregisteredFace: async (faceId: string) => {
		const response = await fetch(
			`${PYTHON_API_URL}/unregister_face/${faceId}`,
			{
				method: "DELETE",
			},
		);

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: "Unregistered face deletion failed" }));
			throw new Error(error.detail);
		}
		return response.json();
	},
};
