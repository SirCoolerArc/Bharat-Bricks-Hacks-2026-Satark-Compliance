import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { question } = await req.json();
  
  if (!question) {
    return NextResponse.json(
      { status: "error", message: "Question parameter is required" },
      { status: 400 }
    );
  }

  try {
    // Call the local FastAPI backend (which runs the pipeline)
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question, history: [] }),
    });

    if (!response.ok) {
      throw new Error(`FastAPI backend error: ${response.statusText}`);
    }

    // The FastAPI backend responds with a Server-Sent Events (SSE) stream.
    // We will accumulate the chunks into a unified JSON structure for the frontend.
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    let completeText = "";
    let dataTablesGenerated: string[] = [];
    let ragSourcesGenerated: any[] = [];
    let rowCountGenerated = 150031;

    if (reader) {
      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunkString = decoder.decode(value);
          const lines = chunkString.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.substring(6).trim();
              if (dataStr) {
                try {
                  const event = JSON.parse(dataStr);
                  if (event.type === "meta") {
                    dataTablesGenerated = event.data_tables_used || [];
                    ragSourcesGenerated = event.rag_sources || [];
                    rowCountGenerated = event.row_count || 150031;
                  } else if (event.type === "text") {
                    completeText += event.content;
                  }
                } catch (e) {
                  // ignore parse errors for partial chunks
                }
              }
            }
          }
        }
      }
    }

    // Reconstruct the JSON response for Next.js frontend ChatPanel.tsx
    const chatbotResult = {
      status: "success",
      data: {
        response: completeText,
        sources: ragSourcesGenerated.map(s => ({
          doc_id: s.document_name,
          snippet: s.snippet,
          score: s.similarity_score
        })),
        meta: dataTablesGenerated.length > 0 ? {
          tables_queried: dataTablesGenerated,
          row_count: rowCountGenerated,
          insights_generated: `Directly analyzed ${dataTablesGenerated.join(', ')} for this query.`
        } : null
      }
    };

    return NextResponse.json(chatbotResult);
  } catch (error) {
    console.error("Chatbot API error:", error);
    return NextResponse.json(
      { 
        status: "error", 
        message: error instanceof Error ? error.message : "Unknown error" 
      },
      { status: 500 }
    );
  }
}

