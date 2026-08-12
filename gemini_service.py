import os
import logging
import re
import time
from datetime import datetime

DEFAULT_GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
GROQ_MODEL_FALLBACKS = (
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'mixtral-8x7b-32768',
)


class GroqService:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY', '').strip()
        self.model = os.environ.get('GROQ_MODEL', DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as exc:
                logging.error('Failed to initialize Groq client: %s', exc)
        else:
            logging.warning('GROQ_API_KEY not found in environment')

    def _generate(self, prompt, temperature=0.7, max_tokens=8192):
        if not self.client:
            return None

        models = [self.model] + [m for m in GROQ_MODEL_FALLBACKS if m != self.model]
        for model_name in models:
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[{'role': 'user', 'content': prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    text = response.choices[0].message.content
                    if text and text.strip():
                        return text.strip()
                except Exception as exc:
                    err = str(exc).lower()
                    logging.error('Groq error model=%s attempt=%s: %s', model_name, attempt + 1, exc)
                    if '429' in err or 'rate' in err:
                        time.sleep(3 + attempt * 3)
                        continue
                    break
        return None

    def generate_comprehensive_report(self, question, category=None, subcategory=None, index_content=None, include_all=False):
        sections = self._get_sections_meta()

        html = f"""
        <div class="report-content" data-question="{question}" data-category="{category or 'Business Intelligence'}" data-subcategory="{subcategory or 'Market Analysis'}">
            <div class="alert alert-primary mb-4">
                <h4 class="mb-2"><i class="fas fa-microscope me-2"></i>IDA Elite Intelligence Protocol</h4>
                <p class="mb-1"><strong>Topic:</strong> {question}</p>
                <p class="mb-0 small text-muted">Click each section to generate a unique, deep-dive analysis grounded in real-world data.</p>
            </div>
        """

        for i, (name, _) in enumerate(sections):
            html += f"""
            <div class="section-wrapper" data-section-id="{i}">
                <h2 class="section-header" onclick="loadSection({i})">
                    <span>{name}</span>
                    <i class="fas fa-chevron-down"></i>
                </h2>
                <div id="section-content-{i}" class="section-content">
                    <div class="loader-container text-center p-5" style="display: none;">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 text-muted">Generating unique research for "{question}"...</p>
                    </div>
                    <div class="content-area"></div>
                </div>
            </div>
            """

        html += '</div>'
        return html

    def generate_section(self, question, category, subcategory, section_id):
        if not self.client:
            return self._get_hardcoded_grounded_fallback('API Error', question)

        sections = self._get_sections_meta()
        if section_id < 0 or section_id >= len(sections):
            return "<p class='text-danger'>Invalid section ID.</p>"

        name, guidance = sections[section_id]
        timestamp = datetime.now().strftime('%H:%M:%S')

        prompt = f"""
        ACT AS: A senior research director.
        TOPIC: "{question}"
        SECTION: "{name}"

        UNIQUENESS GUIDELINES ({timestamp}):
        1. Write 20-25 high-density professional sentences.
        2. NO BOILERPLATE. Start immediately with technical data.
        3. Use real companies and specific numbers.
        4. Focus exclusively on "{question}".

        {guidance.format(question=question, category=category, subcategory=subcategory)}
        """

        text = self._generate(prompt, temperature=0.5, max_tokens=4096)
        if text:
            return self._format_markdown_to_html(text)
        return self._get_hardcoded_grounded_fallback(name, question)

    def generate_execution_plan(self, event_type, problem_type, budget, currency, region, timeline):
        if not self.client:
            logging.error('Groq client not initialized')
            return None

        prompt = f"""
        ACT AS: Senior Strategy Consultant & Project Manager.
        TOPIC: "{event_type}"
        PROBLEM: "{problem_type}"
        BUDGET: {budget} {currency}
        REGION: {region}
        TIMELINE: {timeline}

        Generate a professional 14-section execution plan in Markdown.
        Each section MUST be detailed with specific real-world data, vendors, and costs for {region}.

        SECTIONS:
        1. Executive Summary
        2. Project Flowchart (ASCII diagram)
        3. Key Timelines & Milestones
        4. Implementation Phases
        5. Detailed Budget Breakdown
        6. Expenditure Segregation
        7. Vendor Recommendations
        8. Change Management & Training
        9. Quality Assurance & Testing
        10. Risk & Opportunity Assessment
        11. Geographic Compliance & Legal
        12. Success Criteria & KPIs
        13. Next Steps & 30-Day Action Plan
        14. Innovative Ideas & Scalability

        Use Markdown headers (#, ##, ###) for each section.
        """
        return self._generate(prompt, temperature=0.7, max_tokens=8192)

    def generate_chat_response(self, user_message):
        if not self.client:
            return "I'm sorry, I'm currently disconnected from my AI core. Please try again later."

        prompt = f"""
        ACT AS: IDA Assistant, an elite AI consultant for the Intelligent Data Analytics (IDA) platform.
        USER QUESTION: "{user_message}"

        ABOUT IDA:
        - Research Analytics: /analyse
        - Analysis Reports: /analysis-reports
        - Financial Tools: /financial-tools
        - Project Management: /project-management
        - Buy Credits: /buy-credits

        Answer helpfully in 2-3 sentences and point to the relevant page when useful.
        """
        text = self._generate(prompt, temperature=0.6, max_tokens=512)
        return text or "I'm here to help you navigate IDA! Start on the Analyse page for research projects."

    def generate_competitive_analysis(self, idea, industry, location):
        if not self.client:
            logging.error('Groq API key not set')
            return None

        prompt = f"""
ACT AS: A senior market research analyst.

Business Idea: {idea}
Industry: {industry}
Location: {location}

Generate a detailed competitive analysis in Markdown with sections for:
Market Overview, Direct Competitors, Indirect Competitors, Positioning Map,
Customer Segments, Pricing Patterns, SWOT, Differentiation Strategy,
Entry Strategy, and Key Success Factors.

Use real company names and specific data where possible.
"""
        return self._generate(prompt, temperature=0.4, max_tokens=8192)

    def _get_sections_meta(self):
        return [
            ('1. EXECUTIVE SUMMARY & STRATEGIC OVERVIEW', 'Provide a definitive executive briefing on {question}.'),
            ('2. GLOBAL MARKET SIZE & GROWTH DYNAMICS', 'Provide the TAM for {question}.'),
            ('3. CORE PRODUCT ANALYSIS & VALUE PROPOSITION', 'Break down the unit of value for {question}.'),
            ('4. ADVANCED TECHNOLOGY TRENDS & R&D PIPELINE', 'Identify R&D priorities for {question}.'),
            ('5. COMPETITIVE LANDSCAPE: DEEP ANALYSIS', 'Name the top 7 global leaders in {question}.'),
            ('6. MICRO-SEGMENTATION: GRANULAR ANALYSIS', 'Profile early adopters vs late majority for {question}.'),
            ('7. GEOGRAPHIC PENETRATION: REGIONAL HUBS', 'Analyze India, SE Asia, and US for {question}.'),
            ('8. QUARTERLY FINANCIAL PROJECTIONS', 'Model CAPEX/OPEX for {question}.'),
            ('9. SWOT ANALYSIS: INTERNAL & EXTERNAL FACTORS', 'Technical SWOT for {question}.'),
            ('10. RISK ASSESSMENT & MITIGATION STRATEGY', 'Tier 1 risks for {question}.'),
            ('11. REGULATORY COMPLIANCE & LEGAL FRAMEWORK', 'Laws governing {question}.'),
            ('12. SUPPLY CHAIN LOGISTICS & EFFICIENCY', 'Trace materials/data for {question}.'),
            ('13. CONSUMER BEHAVIOR & ADOPTION PATTERNS', 'Psychology of purchase for {question}.'),
            ('14. DISRUPTIVE OPPORTUNITIES & FUTURE ROADMAP', 'Predict 2035 state of {question}.'),
            ('15. STRATEGIC RECOMMENDATIONS & ACTION PLAN', '12-month implementation checklist.'),
            ('16. INVESTMENT READINESS & ROI PROJECTIONS', 'Exit landscape for {question}.'),
            ('17. SUSTAINABILITY, CIRCULAR ECONOMY & ESG', 'ESG for {question}.'),
            ('18. FINAL CRITICAL ANALYSIS & SYNTHESIS', 'Final verdict on {question}.'),
        ]

    def _format_markdown_to_html(self, text):
        content_html = re.sub(
            r'###\s*(.*?)(?:\n|$)',
            r'<h5 class="mt-4 mb-3 text-info"><i class="fas fa-chevron-circle-right me-2 small"></i>\1</h5>',
            text,
        )
        content_html = re.sub(r'\*\*(.*?)\*\*', r'<strong class="text-warning">\1</strong>', content_html)
        content_html = '<p>' + content_html.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
        return content_html.replace('<p></p>', '')

    def _get_hardcoded_grounded_fallback(self, section_name, question):
        return f"""
        <h5 class="mt-4 mb-3 text-info"><i class="fas fa-microscope me-2 small"></i>Analytical Data for: {question}</h5>
        <p>The {section_name} for <strong>{question}</strong> is currently seeing a significant shift in 2025.</p>
        <p>For more detailed technical specifications regarding {section_name}, please reload this section.</p>
        """


# Legacy import names used across routes/templates
GeminiService = GroqService


def test_groq_connection():
    try:
        service = GroqService()
        if not service.client:
            return False
        result = service._generate('Reply with exactly: OK', temperature=0, max_tokens=8)
        return bool(result)
    except Exception as exc:
        logging.error('Groq connection test failed: %s', exc)
        return False


def test_gemini_connection():
    return test_groq_connection()