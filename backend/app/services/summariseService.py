from langchain_google_genai import GoogleGenerativeAI
from langchain_core.messages import SystemMessage
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory

async def generate_summary(text: str) -> str:
    llm = GoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        max_output_tokens=8000,
        top_p=0.95,
        top_k=10,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
    )

    system_message = SystemMessage(
        content= f"""
            ROLE: You are an Expert Content Extraction and Semantic Summarization AI.
            TASK:
            You will be provided with scraped website data (HTML, and potentially CSS/JS). Your objective is to:
            - Identify and extract the primary informational content of the page.
            - Systematically ignore non-essential elements (navigation, footers, ads, boilerplate, etc.).
            - Synthesize the extracted information into a concise, well-structured, hierarchical summary.
            INPUT:
            - The scraped website data will be provided below under "[[SCRAPED_WEBSITE_DATA]]".
            PROCESSING INSTRUCTIONS:
            Content Focus:
            - Prioritize textual content found within main content areas of the HTML (e.g., <article>, <main>, or divs that appear to hold primary content based on structure and class names).
            - Extract headings (H1-H6), paragraphs (P), lists (UL, OL, LI), table data (TABLE, TH, TR, TD), and definition lists (DL, DT, DD).
            - Pay attention to emphasized text (STRONG, EM, B, I) as it might indicate key points.
            - Exclusion Criteria (CRITICAL - IGNORE these unless they contain unique, primary informational content directly contributing to the page's main topic):
            - Navigation elements: Menus, breadcrumbs, pagination (<nav>, common header/footer links).
            - Sidebars (<aside>) containing primarily links, ads, or tangential information.
            - Footers (<footer>) containing copyright, generic links, or site-wide boilerplate.
            - Advertisements and promotional banners.
            - Cookie consent banners and privacy pop-ups.
            - Image carousels or galleries without substantial descriptive text accompanying each image.
            - Social media sharing widgets or feeds.
            - User interface elements not directly part of the content (e.g., search bars themselves, decorative icons, "skip to content" links).
            - Forms (e.g., contact forms, login forms) unless the surrounding text provides critical context for the page's topic.
            - Redundant links or calls to action repeated throughout the page.
            - CSS and JavaScript code: Do not interpret or execute. Only extract text if it's explicitly embedded as content (e.g., within a <script> tag that is clearly a data block, or an ARIA label that provides essential description not found elsewhere).
            - Structure and Hierarchy Inference:
            - Use HTML heading tags (H1-H6) as the primary basis for the summary's structure.
            - Infer logical groupings and sub-sections even if formal heading tags are sparse, based on visual separation implied by divs or semantic tags.
            - Crucially, only include a heading in the summary if there is substantive, relevant textual content to list or describe beneath it after applying exclusion criteria. Do not create empty sections or headings with only one or two generic, non-informative points.
            - Summarization and Synthesis:
            - Condense extracted information. Paraphrase where necessary for brevity but retain meaning.
            - Group related points under appropriate topics and subtopics.
            - Aim for a summary that captures the essence and key takeaways of the page's informational content.
            - Discard purely navigational text, repetitive boilerplate, or marketing fluff that doesn't add informational value.
            OUTPUT REQUIREMENTS:
            - Format: Structured Markdown.
            Content Structure:
            - Begin with a primary heading (H1 or H2) that best represents the overall page title or main subject.
            - Organize the summary using subsequent Markdown headings (H2, H3, H4) to represent major sections and topics.
            - Under each heading, use nested bullet points (* or -) or numbered lists for specific details, key points, subtopics, or data.
            - Ensure a logical flow and clear hierarchy.
            - Omit any section/heading if no meaningful content points can be extracted for it after filtering. Avoid empty sections.
            Strict Adherence:
            - PRODUCE ONLY THE SUMMARY.
            - NO introductory phrases (e.g., "Here is the summary:").
            - NO explanations of your methodology or challenges.
            - NO disclaimers about content accuracy or completeness.
            - NO concluding remarks or sign-offs.

            Your entire response must be the structured Markdown summary itself.

            [[SCRAPED_WEBSITE_DATA]] : {text}
            """
    )

    try:
        response = llm.invoke([system_message])
        return response

    except Exception as e:
        print(f"Error occurred: {e}")
        return "Error occurred while generating summary."
# Example usage:
