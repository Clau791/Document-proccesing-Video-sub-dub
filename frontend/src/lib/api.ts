export const BASE_URL = 'http://localhost:5000';
export const API_URL = `${BASE_URL}/api`;

export type UploadExtra = Record<string, string | Blob | undefined>;

export const uploadFile = async (
  endpoint: string,
  file: File,
  additionalData?: UploadExtra
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      if (value !== undefined) formData.append(key, value);
    });
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let error = 'Upload failed';
    try {
      const data = await response.json();
      error = data.error || error;
    } catch {
      /* ignore */
    }
    throw new Error(error);
  }

  return response.json();
};
