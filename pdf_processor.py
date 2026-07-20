import PyPDF2
import re
import logging
from models import IndexContent
from app import db

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.sections = {
            'INTRODUCTION': [],
            'UNDERSTANDING': [],
            'PRODUCT': [],
            'MARKET SEGMENTATION': [],
            'COMPETITIVE LANDSCAPE': [],
            'APPLICATION': [],
            'FINANCIALS': [],
            'MARKET OPPORTUNITIES': [],
            'INVESTMENT ANALYSIS': []
        }
    
    def extract_text(self):
        """Extract text from PDF file"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logging.error(f"Error extracting PDF text: {e}")
            return ""
    
    def parse_content(self, text):
        """Parse the extracted text into structured sections"""
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        # Define section patterns
        section_patterns = {
            'INTRODUCTION': r'^INTRODUCTION',
            'UNDERSTANDING': r'^UNDERSTANDING',
            'PRODUCT': r'^PRODUCT',
            'MARKET SEGMENTATION': r'^MARKET SEGMENTATION',
            'COMPETITIVE LANDSCAPE': r'^COMPETITIVE LANDSCAPE',
            'APPLICATION': r'^APPLICATION',
            'FINANCIALS': r'^FINANCIALS',
            'MARKET OPPORTUNITIES': r'^MARKET OPPORTUNITIES',
            'INVESTMENT ANALYSIS': r'^INVESTMENT ANALYSIS'
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts a new section
            section_found = False
            for section_name, pattern in section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    # Save previous section content
                    if current_section and current_content:
                        self.sections[current_section] = current_content
                    
                    current_section = section_name
                    current_content = []
                    section_found = True
                    break
            
            if not section_found and current_section:
                current_content.append(line)
        
        # Save the last section
        if current_section and current_content:
            self.sections[current_section] = current_content
    
    def get_dropdown_options(self):
        """Generate dropdown options for general research analysis"""
        categories = {
            'Product & Market Analysis': [
                'Market Overview',
                'Market Drivers',
                'Market Restraints',
                'Market Movements',
                'Porter\'s 5 Force Model',
                'Government Regulations',
                'Technology Innovations',
                'COVID-19 Impact',
                'Current Landscape'
            ],
            'Market Segmentation': [
                'By Geography',
                'By Demographics',
                'By Industry Vertical',
                'By Company Size',
                'By Technology Stack',
                'By Price Point',
                'By Distribution Channel'
            ],
            'Competitive Analysis': [
                'Key Player Profiles',
                'Business Strategy',
                'SWOT Analysis',
                'Market Positioning',
                'Competitive Advantages'
            ],
            'Technology & Innovation': [
                'Current Technologies',
                'Emerging Trends',
                'AI Integration',
                'Digital Transformation',
                'Future Innovations'
            ],
            'Financial Analysis': [
                'Investment Requirements',
                'Risk Analysis',
                'Financial Projections',
                'Cost Structure',
                'Revenue Models'
            ],
            'Strategic Opportunities': [
                'Growth Strategies',
                'Market Entry',
                'Partnership Opportunities',
                'Implementation Roadmap',
                'Success Metrics'
            ]
        }
        return categories
    
    def save_to_database(self):
        """Save parsed content to database"""
        try:
            # Clear existing content
            IndexContent.query.delete()
            
            section_number = 1
            for section_name, content_lines in self.sections.items():
                if content_lines:
                    content_text = '\n'.join(content_lines)
                    index_content = IndexContent(
                        section=section_name,
                        content=content_text,
                        section_number=section_number
                    )
                    db.session.add(index_content)
                    section_number += 1
            
            db.session.commit()
            logging.info("PDF content saved to database successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving to database: {e}")
            db.session.rollback()
            return False

def initialize_pdf_content():
    """Initialize PDF content in database with predefined sections"""
    try:
        # Clear existing content
        IndexContent.query.delete()
        
        # Define the content based on the PDF index structure - General research template
        sections_content = {
            'INTRODUCTION': """
            1. An introduction to the topic and research approach
            2. Understanding the research question
            3. Scope and methodology
            4. Initial assessment
            5. Overview of findings
            
            This section provides foundational understanding and context for any research topic.
            """,
            'UNDERSTANDING': """
            1. Final Understanding
            2. Key Takeaways
            3. Key Achievements decided
            4. Scope of study
            
            Deep dive into comprehensive understanding, strategic insights, and research objectives for any domain.
            """,
            'PRODUCT': """
            1. About the Product and Market
            2. Market Overview
            3. Market Drivers
            4. Market Restraints
            5. Market movements
            6. Porter's 5 force model
               a) Threat of New Entrants
               b) Bargaining Power of Buyers/Consumers
               c) Bargaining Power of Suppliers
               d) Threat of Substitute Products
               e) Intensity of Competitive Rivalry
            7. Government and Market Regulations
            8. Impact of Technological Innovations in the Market
            9. Impact of Covid-19
            10. The Fusion of Software and Services by AI
            11. Products in the Market In 2024
            12. Current Landscape in 2024-25
            
            Comprehensive analysis of products/services, market dynamics, competitive forces, and regulatory environment.
            """,
            'MARKET SEGMENTATION': """
            1. Source
            2. Bank
            3. Digital Finance Companies (HFC's)
            4. By Interest Rate (Fixed Rate, Floating Rate)
            5. By Tenure (Up to 5 Years, 6-10 Years, 11-24 Years, 25-30 Years)
            6. Hardware and Networking Equipment
            7. IT Services and Cloud Services
            8. IT Infrastructure/Data Centers
            9. Data Center Storage and Servers
            10. IT Security/Cybersecurity
            11. Application Security, Cloud Security, Data Security
            12. Identity and Access Management
            13. Infrastructure Protection
            14. Integrated Risk Management
            15. Network Security Equipment
            16. Endpoint Security
            17. Communication Services
            18. Small and Medium Enterprises
            19. Large Enterprises
            20. Importance of Credit score
            21. Problem Solving provision
            22. Loanspace market
            23. Value Propositions
            24. Direct sourcing questions from real estate firms
            25. Existing Market analysis
            26. How to Break or enter the market
            27. B2C, B2B, and D2C selling strategies
            
            Detailed market segmentation analysis covering various dimensions of the fintech industry.
            """,
            'COMPETITIVE LANDSCAPE': """
            Key Company Profiles with Business Overview, Offering Portfolio, Financials, Business Strategy and Recent Developments, SWOT analysis:
            1. Fundigo
            2. Upgrade
            3. Valon
            4. Hometap
            5. Affirm
            
            Comprehensive competitive analysis including market positioning and strategic assessment.
            """,
            'APPLICATION': """
            1. Applications existing in the field
            2. Upgrades from 2020
            3. Changes in the field regarding applications
            4. Key takeaways and how to have a mark
            5. Technicals of the application
            6. Security information
            7. User personas and journey
            8. Design language
            9. Development of website then application
            10. Creation of both
            11. Launch strategies
            
            Technical and strategic aspects of fintech application development and deployment.
            """,
            'FINANCIALS': """
            1. What kind of financials go into something like that
            2. Financial futures
            3. Investment clearance
            4. Spendings chart
            5. Risk analysis
            
            Financial planning, investment analysis, and risk assessment for fintech ventures.
            """,
            'MARKET OPPORTUNITIES': """
            1. Brand positioning
            2. What kind of hiring
            3. What kind of build and company
            4. How to improve and move
            5. Retention strategy
            6. Exploring Best business strategies
            7. Plan implementation: development timeline, resource allocation
            8. Structuring with NBC or banks
            9. Global market percentages
            10. Strategic directions
            
            Strategic opportunities and implementation roadmap for market expansion.
            """
        }
        
        section_number = 1
        for section_name, content in sections_content.items():
            index_content = IndexContent(
                section=section_name,
                content=content.strip(),
                section_number=section_number
            )
            db.session.add(index_content)
            section_number += 1
        
        db.session.commit()
        logging.info("PDF content initialized successfully with predefined structure")
        return True
        
    except Exception as e:
        logging.error(f"Error initializing PDF content: {e}")
        db.session.rollback()
        return False
