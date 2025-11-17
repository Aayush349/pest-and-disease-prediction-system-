import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = {
  // Predict disease
  predictDisease: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(
      `${API_BASE_URL}/api/predict/disease`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    
    return response.data;
  },
  
  // Send chat message
  sendMessage: async (message, chatHistory = []) => {
    const response = await axios.post(
      `${API_BASE_URL}/api/chat/message`,
      { message, chat_history: chatHistory }
    );
    
    return response.data;
  },
  
  // Explain detection
  explainDetection: async (detectionResult, question) => {
    const response = await axios.post(
      `${API_BASE_URL}/api/chat/explain`,
      { detection_result: detectionResult, question }
    );
    
    return response.data;
  },
  
  // Get diseases list
  getDiseases: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/predict/diseases`);
    return response.data;
  }
};
