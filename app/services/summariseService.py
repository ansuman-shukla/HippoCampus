from langchain_google_genai import GoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage



def generate_summary(text: str) -> str:
    llm = GoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        max_output_tokens=1000,
        top_p=0.95,
        top_k=1,
        max_retries=3,
        retry_delay=2
    )

    system_message = SystemMessage(
        content= f"""
            ROLE: You are an Expert Content Extraction and Summarization AI.
            TASK:
            - You will be provided with scraped website data, including HTML, CSS, and potentially JavaScript. Your objective is to meticulously analyze this data to extract the core informational content and present it as a structured summary.
            INPUT:
            - The scraped website data will be provided below under "[[SCRAPED_WEBSITE_DATA]]".
            PROCESSING INSTRUCTIONS:
            - Prioritize Content: Focus on extracting textual content, headings, lists, and significant data points from the HTML.
            - Infer Structure: Use HTML tags (H1-H6, P, UL, OL, LI, TABLE, etc.) and layout cues (even if inferred from class names or structure without CSS rendering) to understand the hierarchy and relationship between content elements.
            - Ignore Non-Content Code: Disregard CSS styling rules and JavaScript functionality unless they directly embed or reveal explicit textual content (e.g., text within <script> tags that is clearly content, or ARIA labels that provide descriptive text). Do not attempt to execute or interpret JS logic.
            - Synthesize Information: Condense the extracted information into a logical, hierarchical summary.
            OUTPUT REQUIREMENTS:
            - Format: Structured Markdown.
            Content:
            - Start with a main heading (H1 or H2) representing the overall site/page title or primary purpose.
            - Identify major sections of the website and represent them as subsequent headings (H2, H3).
            - Under each section, list key topics, concepts, or information categories (H3, H4, or bullet points).
            - For each topic, provide specific subtopics, key points, details, or data using nested bullet points (* or -) or numbered lists where appropriate.
            - Aim for conciseness while retaining essential information.
            Strictness:
            - ONLY THE SUMMARY.
            - NO introductory sentences.
            - NO explanations of your process.
            - NO disclaimers.
            - NO concluding remarks.

            Your entire response must be the structured summary itself.
            [[SCRAPED_WEBSITE_DATA]]: {text}
            """
    )

    response = llm.invoke([system_message])

    return response.content
