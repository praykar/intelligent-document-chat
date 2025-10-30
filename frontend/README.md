# Intelligent Document Chat - Frontend

Streamlit-based frontend for the Intelligent Document Chat application. This interface allows users to upload PDF documents and interact with them using natural language queries powered by Google Gemini API.

## Features

- 📄 **PDF Upload**: Easy drag-and-drop or file selection for PDF documents
- 📊 **Document Statistics**: View document ID, chunk count, page count, and filename
- 💬 **Interactive Chat**: Natural language question answering with context-aware responses
- 🔄 **Query Rephrasing**: See how your queries are optimized for better results
- 📚 **Source Citations**: View the exact document sections used to generate responses
- 💡 **Smart Suggestions**: Get AI-generated follow-up questions to explore topics further
- 🎨 **Clean UI**: Material-inspired design with Streamlit native controls

## Installation

### Prerequisites

- Python 3.8 or higher
- Backend API running (see `../backend/README.md`)

### Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the frontend directory:
   ```bash
   BACKEND_URL=http://localhost:8000
   ```

   Or export the variable:
   ```bash
   export BACKEND_URL=http://localhost:8000
   ```

## Usage

### Starting the Application

Run the Streamlit app:

```bash
streamlit run src/app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Interface

1. **Upload a PDF Document:**
   - Click on the sidebar
   - Use the file uploader to select a PDF
   - Click "Process Document" to upload and analyze

2. **View Document Statistics:**
   - After processing, see document ID, chunk count, pages, and filename
   - These stats help you understand how the document was processed

3. **Chat with Your Document:**
   - Type your question in the chat input box
   - Press Enter to send
   - View the AI-generated response along with:
     - Rephrased query (how the system optimized your question)
     - Source citations (expandable section showing relevant document chunks)
     - Follow-up question suggestions (clickable buttons)

4. **Explore Further:**
   - Click on suggested follow-up questions to continue the conversation
   - Use "Clear Chat History" to start a new conversation
   - Upload a new document to analyze different content

## Configuration

### Environment Variables

- `BACKEND_URL`: Backend API endpoint (default: `http://localhost:8000`)

### Custom Styling

The app includes custom CSS for a polished look. You can modify the styles in `src/app.py` in the `st.markdown()` section with custom CSS.

## Project Structure

```
frontend/
├── src/
│   └── app.py          # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## API Integration

The frontend communicates with the backend through two main endpoints:

### Upload Endpoint
- **POST** `/api/upload`
- Uploads PDF file and returns document metadata
- Response includes: document_id, chunk_count, filename, page_count

### Chat Endpoint
- **POST** `/api/chat`
- Sends user query and receives AI-generated response
- Request payload:
  ```json
  {
    "message": "user query",
    "document_id": "doc_id",
    "history": [{"user": "...", "assistant": "..."}]
  }
  ```
- Response includes:
  - `response`: AI-generated answer
  - `rephrased_query`: Optimized query
  - `sources`: Relevant document chunks with scores
  - `followup_questions`: Suggested next questions

## Technologies Used

- **Streamlit**: Web application framework
- **Requests**: HTTP client for API calls
- **Python-dotenv**: Environment variable management

## Troubleshooting

### Backend Connection Issues

1. Ensure the backend is running:
   ```bash
   # In the backend directory
   uvicorn app.main:app --reload
   ```

2. Check the `BACKEND_URL` environment variable is set correctly

3. Verify the backend is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

### Upload Failures

- Check PDF file is not corrupted
- Ensure file size is within limits
- Check backend logs for processing errors

### Chat Not Responding

- Verify document was successfully uploaded (check for document ID in stats)
- Ensure backend has API keys configured (Gemini API)
- Check browser console for JavaScript errors

## Development

### Running in Development Mode

```bash
streamlit run src/app.py --server.runOnSave true
```

This enables auto-reload when you save changes to the code.

### Adding New Features

1. Modify `src/app.py`
2. Update UI components or add new sections
3. Test with various PDF documents
4. Update this README with new features

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See the main project LICENSE file.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review backend logs for API errors
