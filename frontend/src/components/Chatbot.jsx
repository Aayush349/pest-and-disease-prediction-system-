import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, Loader2, ImageIcon, Bot, User, Trash2, Download } from 'lucide-react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import './Chatbot.css';

const API_BASE_URL = 'http://localhost:8000/api';

export function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hello! I\'m AgroGuard AI, your intelligent agricultural companion.\n\nI can help you:\n✓ Detect crop diseases from images\n✓ Provide treatment recommendations\n✓ Answer farming questions\n✓ Explain prevention strategies\n\nStart by uploading a crop image or asking a question!',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [currentPrediction, setCurrentPrediction] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file size (10MB max)
      if (file.size > 10485760) {
        toast.error('Image size must be less than 10MB');
        return;
      }
      
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      toast.success('Image selected! Click send to analyze.');
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() && !selectedImage) {
      toast.error('Please type a message or upload an image');
      return;
    }

    // Add user message
    const userMessage = {
      role: 'user',
      content: input || '📸 Analyzing image...',
      image: imagePreview,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      if (selectedImage) {
        // Detect disease
        const formData = new FormData();
        formData.append('file', selectedImage);
        
        const predictionRes = await axios.post(
          `${API_BASE_URL}/predict/disease`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );

        if (!predictionRes.data.success) {
          throw new Error(predictionRes.data.error);
        }

        const prediction = predictionRes.data.data;
        setCurrentPrediction(prediction);

        // Get explanation
        const explanationRes = await axios.post(
          `${API_BASE_URL}/chat/explain-disease`,
          {
            disease: prediction.disease,
            image_analysis: prediction
          }
        );

        if (!explanationRes.data.success) {
          throw new Error('Failed to get explanation');
        }

        // Add assistant response
        const assistantMessage = {
          role: 'assistant',
          content: explanationRes.data.data.explanation,
          detection: prediction,
          treatment: explanationRes.data.data.treatment_steps,
          prevention: explanationRes.data.data.prevention_tips,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, assistantMessage]);
        toast.success('Analysis complete!');
        
      } else {
        // Chat message
        const chatRes = await axios.post(
          `${API_BASE_URL}/chat/message`,
          {
            message: input,
            image_analysis: currentPrediction
          }
        );

        if (!chatRes.data.success) {
          throw new Error('Chat failed');
        }

        const assistantMessage = {
          role: 'assistant',
          content: chatRes.data.data.response,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
      
      setSelectedImage(null);
      setImagePreview(null);
      
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.response?.data?.detail || 'Failed. Please try again.');
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ ' + (error.response?.data?.detail || 'An error occurred. Please try again.'),
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    if (window.confirm('Clear all messages?')) {
      setMessages([messages[0]]);
      setCurrentPrediction(null);
      toast.success('Chat cleared');
    }
  };

  const downloadChat = () => {
    const chatText = messages
      .map(m => `[${m.role.toUpperCase()}]: ${m.content}\n`)
      .join('\n');
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(chatText));
    element.setAttribute('download', `agroguard-chat-${new Date().toISOString()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Chat downloaded!');
  };

  return (
    <div className="chatbot-container">
      <Toaster position="top-right" />
      
      {/* Header */}
      <div className="chatbot-header">
        <div className="header-content">
          <Bot className="header-icon" />
          <div>
            <h1>AgroGuard AI Assistant</h1>
            <p>Intelligent Crop Disease Detection & Advisory</p>
          </div>
        </div>
        <div className="header-actions">
          <button onClick={downloadChat} className="btn-small" title="Download chat">
            <Download size={18} />
          </button>
          <button onClick={clearChat} className="btn-small" title="Clear chat">
            <Trash2 size={18} />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            <div className={`message-bubble ${msg.role}`}>
              {msg.image && (
                <img src={msg.image} alt="Uploaded" className="message-image" />
              )}

              <p className="message-text">{msg.content}</p>

              {/* Detection Card */}
              {msg.detection && (
                <div className="detection-card">
                  <div className="card-title">🔍 Detection Result</div>
                  <div className="card-stats">
                    <div className="stat">
                      <span className="stat-label">Disease:</span>
                      <span className="stat-value">{msg.detection.disease}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Confidence:</span>
                      <span className="stat-value">{(msg.detection.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Severity:</span>
                      <span className="stat-value">{msg.detection.severity}/100</span>
                    </div>
                  </div>
                  <div className="progress-bar">
                    <div
                      className={`progress-fill ${msg.detection.severity > 70 ? 'high' : msg.detection.severity > 40 ? 'medium' : 'low'}`}
                      style={{width: `${msg.detection.severity}%`}}
                    />
                  </div>
                </div>
              )}

              {/* Treatment Steps */}
              {msg.treatment && msg.treatment.length > 0 && (
                <div className="treatment-card">
                  <div className="card-title">💊 Treatment Steps</div>
                  <ol className="treatment-list">
                    {msg.treatment.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Prevention Tips */}
              {msg.prevention && msg.prevention.length > 0 && (
                <div className="prevention-card">
                  <div className="card-title">🛡️ Prevention Tips</div>
                  <ul className="prevention-list">
                    {msg.prevention.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}

              <span className="message-time">
                {msg.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-wrapper assistant">
            <div className="message-bubble assistant">
              <Loader2 className="spinner" />
              <p>Analyzing...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-container">
        {imagePreview && (
          <div className="image-preview-container">
            <img src={imagePreview} alt="Preview" className="image-preview" />
            <button
              onClick={() => {
                setSelectedImage(null);
                setImagePreview(null);
              }}
              className="remove-image"
            >
              ×
            </button>
          </div>
        )}

        <div className="input-row">
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn-input btn-upload"
            title="Upload image"
          >
            <Upload size={20} />
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
            placeholder="Ask about crop diseases, upload an image, or type..."
            className="input-field"
          />

          <button
            onClick={handleSendMessage}
            disabled={loading || (!input.trim() && !selectedImage)}
            className="btn-input btn-send"
          >
            {loading ? (
              <Loader2 className="spinner-small" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
