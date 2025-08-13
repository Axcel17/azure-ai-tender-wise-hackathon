"""RUC Validation Plugin for TenderWise - Tender Analysis System
Enhanced contractor verification for Ecuadorian public procurement."""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
from semantic_kernel.functions import kernel_function

class RucValidationPlugin:
    """Plugin for comprehensive RUC validation and contractor verification for tender analysis."""
    
    def __init__(self):
        """Initialize the RUC validation plugin with Ecuador-specific data."""
        # Ecuador provinces for RUC validation (complete and updated)
        self.ecuador_provinces = {
            "01": "Azuay", "02": "Bolívar", "03": "Cañar", "04": "Carchi",
            "05": "Cotopaxi", "06": "Chimborazo", "07": "El Oro", "08": "Esmeraldas",
            "09": "Guayas", "10": "Imbabura", "11": "Loja", "12": "Los Ríos",
            "13": "Manabí", "14": "Morona Santiago", "15": "Napo", "16": "Pastaza",
            "17": "Pichincha", "18": "Tungurahua", "19": "Zamora Chinchipe",
            "20": "Galápagos", "21": "Sucumbíos", "22": "Orellana", "23": "Santo Domingo",
            "24": "Santa Elena"
        }
        
        # Enhanced taxpayer types with eligibility for public contracts
        self.taxpayer_types = {
            0: {"name": "Sector público", "eligible": False, "description": "Entidades del sector público"},
            1: {"name": "Persona natural", "eligible": True, "description": "Persona natural con actividad económica"},
            2: {"name": "Persona natural", "eligible": True, "description": "Persona natural con actividad económica"},
            3: {"name": "Persona natural", "eligible": True, "description": "Persona natural con actividad económica"},
            4: {"name": "Persona natural", "eligible": True, "description": "Persona natural con actividad económica"},
            5: {"name": "Persona natural", "eligible": True, "description": "Persona natural con actividad económica"},
            6: {"name": "Sociedad privada", "eligible": True, "description": "Empresa privada con capacidad contractual"},
            9: {"name": "Jurídica extranjera", "eligible": True, "description": "Empresa extranjera registrada en Ecuador"}
        }
        
        # Contract amount thresholds for additional validations (USD)
        self.contract_thresholds = {
            "small": 100000,      # < $100K - Contratos menores
            "medium": 1000000,    # $100K - $1M - Contratos medianos
            "large": 10000000,    # $1M - $10M - Contratos grandes
            "mega": 50000000      # > $10M - Mega contratos
        }
        
        # SERCOP and official sources for enhanced searches
        self.official_sources = [
            "sercop.gob.ec", "compraspublicas.gob.ec", "sri.gob.ec",
            "supercias.gob.ec", "serviciospublicos.gob.ec"
        ]

    @kernel_function(
        description="Comprehensive RUC validation for Ecuadorian contractors in public procurement",
        name="validate_ruc_comprehensive"
    )
    def validate_ruc_comprehensive(self, ruc: str, contract_amount: str = "0") -> str:
        """
        Comprehensive RUC validation including eligibility for public contracts.
        
        Args:
            ruc: RUC number to validate
            contract_amount: Contract amount in USD for capacity assessment
            
        Returns:
            JSON string with comprehensive validation results
        """
        try:
            # Clean inputs
            clean_ruc = re.sub(r'\D', '', str(ruc))
            amount = float(contract_amount) if contract_amount else 0
            
            validation_result = {
                "ruc": clean_ruc,
                "original_input": str(ruc),
                "contract_amount": amount,
                "valid": False,
                "eligible_for_contracts": False,
                "errors": [],
                "warnings": [],
                "details": {},
                "capacity_assessment": {},
                "validation_date": datetime.now().isoformat(),
                "validation_level": "comprehensive"
            }
            
            # Basic format validation
            format_validation = self._validate_basic_format(clean_ruc)
            if not format_validation["valid"]:
                validation_result["errors"].extend(format_validation["errors"])
                return json.dumps(validation_result, ensure_ascii=False, indent=2)
            
            # Enhanced province validation
            province_validation = self._validate_province(clean_ruc)
            validation_result["details"].update(province_validation)
            
            # Enhanced taxpayer type validation
            taxpayer_validation = self._validate_taxpayer_type(clean_ruc)
            validation_result["details"].update(taxpayer_validation)
            if not taxpayer_validation["eligible_for_contracts"]:
                validation_result["warnings"].append(
                    f"Tipo de contribuyente '{taxpayer_validation['taxpayer_name']}' tiene limitaciones para contratos públicos"
                )
            
            # Mathematical verification digit validation
            digit_validation = self._validate_verification_digit(clean_ruc)
            if not digit_validation["valid"]:
                validation_result["errors"].extend(digit_validation["errors"])
                return json.dumps(validation_result, ensure_ascii=False, indent=2)
            
            validation_result["details"]["verification_digit"] = digit_validation["calculated_digit"]
            
            # Contract capacity assessment
            if amount > 0:
                capacity_assessment = self._assess_contract_capacity(clean_ruc, amount)
                validation_result["capacity_assessment"] = capacity_assessment
                
                if capacity_assessment["requires_additional_validation"]:
                    validation_result["warnings"].extend(capacity_assessment["warnings"])
            
            # If we reach here, RUC is technically valid
            validation_result["valid"] = True
            validation_result["eligible_for_contracts"] = taxpayer_validation["eligible_for_contracts"]
            
            # Generate specific recommendations
            validation_result["recommendations"] = self._generate_validation_recommendations(validation_result)
            
            return json.dumps(validation_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "ruc": str(ruc),
                "valid": False,
                "eligible_for_contracts": False,
                "errors": [f"Error crítico en validación de RUC: {str(e)}"],
                "validation_date": datetime.now().isoformat(),
                "validation_level": "error"
            }, ensure_ascii=False)

    @kernel_function(
        description="Generate enhanced search strategy for contractor verification",
        name="generate_contractor_search_strategy"
    )
    def generate_contractor_search_strategy(self, ruc: str, razon_social: str, contract_type: str = "obra") -> str:
        """
        Generate comprehensive search strategy for contractor verification.
        
        Args:
            ruc: RUC number of contractor
            razon_social: Company name
            contract_type: Type of contract (obra, servicio, bien)
            
        Returns:
            JSON string with enhanced search strategy
        """
        try:
            # Clean inputs
            clean_ruc = re.sub(r'\D', '', str(ruc))
            clean_name = razon_social.strip()
            
            # Generate contract-specific search queries
            search_strategy = {
                "contractor_info": {
                    "ruc": clean_ruc,
                    "razon_social": clean_name,
                    "contract_type": contract_type
                },
                "search_phases": {
                    "phase_1_basic_verification": [
                        f'"{clean_name}" RUC {clean_ruc} Ecuador',
                        f'{clean_name} empresa Ecuador superintendencia compañías',
                        f'RUC {clean_ruc} sri.gob.ec estado contribuyente'
                    ],
                    "phase_2_public_contracts": [
                        f'"{clean_name}" contratos públicos SERCOP Ecuador',
                        f'{clean_name} adjudicaciones licitaciones Ecuador',
                        f'RUC {clean_ruc} compraspublicas.gob.ec portal',
                        f'"{clean_name}" obras públicas prefectura municipio'
                    ],
                    "phase_3_capacity_experience": [
                        f'"{clean_name}" experiencia {contract_type} Ecuador',
                        f'{clean_name} proyectos construcción infraestructura',
                        f'"{clean_name}" certificaciones ISO calidad'
                    ],
                    "phase_4_reputation_risks": [
                        f'"{clean_name}" noticias problemas Ecuador',
                        f'{clean_name} sanciones multas SERCOP',
                        f'"{clean_name}" inhabilitar contratación pública',
                        f'{clean_name} demandas juicios legales'
                    ]
                },
                "priority_sources": {
                    "official_government": [
                        "sercop.gob.ec - Portal de compras públicas",
                        "sri.gob.ec - Servicio de Rentas Internas",
                        "supercias.gob.ec - Superintendencia de Compañías",
                        "compraspublicas.gob.ec - Sistema de contratación"
                    ],
                    "business_verification": [
                        "ekosnegocios.com - Información empresarial",
                        "revistalideres.ec - Noticias empresariales",
                        "expreso.ec - Información comercial"
                    ],
                    "legal_compliance": [
                        "funcionjudicial.gob.ec - Sistema judicial",
                        "contraloria.gob.ec - Contraloría General"
                    ]
                },
                "data_extraction_targets": {
                    "basic_info": [
                        "Razón social completa y exacta",
                        "RUC y estado del contribuyente",
                        "Dirección principal y sucursales",
                        "Representante legal actual",
                        "Actividad económica principal"
                    ],
                    "contract_capacity": [
                        "Experiencia en contratos públicos",
                        "Montos de contratos anteriores",
                        "Tipos de obras o servicios ejecutados",
                        "Certificaciones técnicas",
                        "Personal técnico calificado"
                    ],
                    "financial_indicators": [
                        "Capital social registrado",
                        "Estados financieros públicos",
                        "Patrimonio empresarial",
                        "Indicadores de liquidez"
                    ],
                    "risk_factors": [
                        "Sanciones por incumplimiento",
                        "Multas o penalizaciones",
                        "Inhabilitaciones vigentes",
                        "Procesos judiciales pendientes",
                        "Antecedentes negativos"
                    ]
                },
                "analysis_framework": {
                    "positive_indicators": [
                        "empresa activa", "habilitado SERCOP", "certificado ISO",
                        "experiencia comprobada", "obras entregadas", "cumplimiento contractual",
                        "reconocimientos", "premios calidad", "responsabilidad social",
                        "equipos especializados", "personal calificado"
                    ],
                    "warning_indicators": [
                        "atrasos menores", "observaciones técnicas", "cambio directivos",
                        "empresa nueva", "experiencia limitada", "recursos justos"
                    ],
                    "risk_indicators": [
                        "sancionado", "inhabilitado", "multado", "incumplimiento",
                        "demandado", "clausurado", "suspendido", "investigado",
                        "controversias", "problemas financieros", "obras abandonadas"
                    ]
                },
                "search_timestamp": datetime.now().isoformat(),
                "estimated_search_time": "15-20 minutos para verificación completa"
            }
            
            return json.dumps(search_strategy, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Error generando estrategia de búsqueda: {str(e)}",
                "basic_search": [f'"{razon_social}" RUC {ruc} Ecuador'],
                "search_timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)

    @kernel_function(
        description="Analyze search results with enhanced intelligence for contractor assessment",
        name="analyze_contractor_intelligence"
    )
    def analyze_contractor_intelligence(self, search_results: str, ruc_validation: str, contract_amount: str = "0") -> str:
        """
        Enhanced analysis of search results for comprehensive contractor assessment.
        
        Args:
            search_results: Text with search results from Bing
            ruc_validation: JSON string with RUC validation results
            contract_amount: Contract amount for capacity assessment
            
        Returns:
            JSON string with comprehensive contractor assessment
        """
        try:
            # Parse inputs
            ruc_data = json.loads(ruc_validation) if ruc_validation else {}
            amount = float(contract_amount) if contract_amount else 0
            
            # Initialize comprehensive assessment
            assessment = {
                "contractor_intelligence": {
                    "ruc_valid": ruc_data.get("valid", False),
                    "eligible_for_contracts": ruc_data.get("eligible_for_contracts", False),
                    "information_quality": self._assess_information_quality(search_results),
                    "overall_rating": "unknown",
                    "confidence_level": "low",
                    "risk_level": "unknown",
                    "contract_amount": amount
                },
                "detailed_findings": {
                    "positive_indicators": [],
                    "warning_indicators": [],
                    "risk_indicators": [],
                    "neutral_information": [],
                    "official_sources_found": []
                },
                "capacity_analysis": {},
                "recommendations": [],
                "next_verification_steps": [],
                "assessment_date": datetime.now().isoformat()
            }
            
            # Immediate rejection if RUC is invalid
            if not ruc_data.get("valid", False):
                assessment["contractor_intelligence"]["overall_rating"] = "rejected"
                assessment["contractor_intelligence"]["risk_level"] = "critical"
                assessment["recommendations"] = [
                    "RECHAZAR INMEDIATAMENTE - RUC inválido",
                    "No proceder con evaluación adicional",
                    "Solicitar corrección de información"
                ]
                return json.dumps(assessment, ensure_ascii=False, indent=2)
            
            # Enhanced search content analysis
            if search_results and len(search_results.strip()) > 50:
                assessment["detailed_findings"] = self._analyze_search_content_enhanced(search_results)
                assessment["contractor_intelligence"]["confidence_level"] = "medium"
                
                # Check for official sources
                official_sources = self._identify_official_sources(search_results)
                assessment["detailed_findings"]["official_sources_found"] = official_sources
                
                if official_sources:
                    assessment["contractor_intelligence"]["confidence_level"] = "high"
            
            # Contract capacity analysis
            if amount > 0:
                capacity_analysis = self._analyze_contract_capacity(
                    assessment["detailed_findings"], ruc_data, amount
                )
                assessment["capacity_analysis"] = capacity_analysis
            
            # Calculate comprehensive ratings
            assessment["contractor_intelligence"]["overall_rating"] = self._calculate_enhanced_rating(
                assessment["detailed_findings"], ruc_data, amount
            )
            
            assessment["contractor_intelligence"]["risk_level"] = self._assess_risk_level(
                assessment["detailed_findings"]
            )
            
            # Generate actionable recommendations
            assessment["recommendations"] = self._generate_enhanced_recommendations(assessment)
            
            # Define next verification steps
            assessment["next_verification_steps"] = self._define_verification_steps(assessment)
            
            return json.dumps(assessment, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Error en análisis de inteligencia del contratista: {str(e)}",
                "contractor_intelligence": {"overall_rating": "requires_manual_review"},
                "assessment_date": datetime.now().isoformat()
            }, ensure_ascii=False)

    @kernel_function(
        description="Generate final contractor verification report for tender evaluation",
        name="generate_final_contractor_report"
    )
    def generate_final_contractor_report(self, ruc_validation: str, contractor_analysis: str, contract_details: str = "{}") -> str:
        """
        Generate comprehensive final contractor verification report.
        
        Args:
            ruc_validation: JSON with RUC validation results
            contractor_analysis: JSON with contractor intelligence analysis
            contract_details: JSON with contract specifics
            
        Returns:
            JSON string with final comprehensive verification report
        """
        try:
            # Parse all inputs
            ruc_data = json.loads(ruc_validation) if ruc_validation else {}
            analysis_data = json.loads(contractor_analysis) if contractor_analysis else {}
            contract_data = json.loads(contract_details) if contract_details else {}
            
            # Generate comprehensive report
            report = {
                "contractor_verification_report": {
                    "report_id": f"CVR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "generation_date": datetime.now().isoformat(),
                    "contractor_ruc": ruc_data.get("ruc", ""),
                    "contract_amount": contract_data.get("monto_total", 0),
                    "verification_status": self._determine_final_status(ruc_data, analysis_data),
                    "report_type": "comprehensive_contractor_verification"
                },
                "executive_summary": {
                    "recommendation": self._generate_executive_recommendation(ruc_data, analysis_data),
                    "key_findings": self._extract_key_findings(analysis_data),
                    "critical_issues": self._identify_critical_issues(analysis_data),
                    "confidence_level": analysis_data.get("contractor_intelligence", {}).get("confidence_level", "low")
                },
                "ruc_technical_validation": {
                    "valid": ruc_data.get("valid", False),
                    "province": ruc_data.get("details", {}).get("province_name", ""),
                    "taxpayer_type": ruc_data.get("details", {}).get("taxpayer_name", ""),
                    "eligible_for_contracts": ruc_data.get("eligible_for_contracts", False),
                    "verification_details": ruc_data.get("details", {})
                },
                "contractor_intelligence_summary": analysis_data.get("contractor_intelligence", {}),
                "findings_analysis": {
                    "positive_aspects": analysis_data.get("detailed_findings", {}).get("positive_indicators", []),
                    "risk_factors": analysis_data.get("detailed_findings", {}).get("risk_indicators", []),
                    "warning_signs": analysis_data.get("detailed_findings", {}).get("warning_indicators", []),
                    "information_sources": analysis_data.get("detailed_findings", {}).get("official_sources_found", [])
                },
                "capacity_assessment": analysis_data.get("capacity_analysis", {}),
                "final_decision": self._make_final_decision(ruc_data, analysis_data),
                "implementation_plan": self._create_implementation_plan(ruc_data, analysis_data),
                "monitoring_requirements": self._define_monitoring_requirements(analysis_data)
            }
            
            return json.dumps(report, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "contractor_verification_report": {
                    "report_id": f"CVR_ERROR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "error": f"Error generando reporte final: {str(e)}",
                    "generation_date": datetime.now().isoformat()
                },
                "final_decision": {
                    "decision": "requires_manual_review",
                    "reason": "Error en el sistema de verificación - revisar manualmente"
                }
            }, ensure_ascii=False)

    # Enhanced helper methods
    
    def _validate_basic_format(self, ruc: str) -> Dict[str, Any]:
        """Enhanced basic format validation."""
        if len(ruc) != 13:
            return {
                "valid": False,
                "errors": [f"RUC debe tener exactamente 13 dígitos, encontrado: {len(ruc)}"]
            }
        
        if not ruc.isdigit():
            return {
                "valid": False,
                "errors": ["RUC debe contener solo números"]
            }
        
        return {"valid": True, "errors": []}
    
    def _validate_province(self, ruc: str) -> Dict[str, Any]:
        """Enhanced province validation."""
        province_code = ruc[:2]
        
        if province_code not in self.ecuador_provinces:
            return {
                "province_code": province_code,
                "province_name": "Código inválido",
                "province_valid": False
            }
        
        return {
            "province_code": province_code,
            "province_name": self.ecuador_provinces[province_code],
            "province_valid": True
        }
    
    def _validate_taxpayer_type(self, ruc: str) -> Dict[str, Any]:
        """Enhanced taxpayer type validation."""
        third_digit = int(ruc[2])
        
        if third_digit not in self.taxpayer_types:
            return {
                "taxpayer_code": third_digit,
                "taxpayer_name": "Tipo inválido",
                "taxpayer_valid": False,
                "eligible_for_contracts": False
            }
        
        taxpayer_info = self.taxpayer_types[third_digit]
        
        return {
            "taxpayer_code": third_digit,
            "taxpayer_name": taxpayer_info["name"],
            "taxpayer_description": taxpayer_info["description"],
            "taxpayer_valid": True,
            "eligible_for_contracts": taxpayer_info["eligible"]
        }
    
    def _validate_verification_digit(self, ruc: str) -> Dict[str, Any]:
        """Enhanced verification digit calculation and validation."""
        calculated_digit = self._calculate_verification_digit(ruc)
        actual_digit = int(ruc[12])
        
        return {
            "valid": calculated_digit == actual_digit,
            "calculated_digit": calculated_digit,
            "actual_digit": actual_digit,
            "errors": [] if calculated_digit == actual_digit else [
                f"Dígito verificador incorrecto. Calculado: {calculated_digit}, Encontrado: {actual_digit}"
            ]
        }
    
    def _calculate_verification_digit(self, ruc: str) -> int:
        """Calculate RUC verification digit using Ecuador's official algorithms."""
        if len(ruc) != 13:
            return -1
        
        third_digit = int(ruc[2])
        
        if third_digit < 6:
            # Natural person algorithm (Módulo 10)
            coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            for i in range(9):
                value = int(ruc[i]) * coefficients[i]
                if value >= 10:
                    value = (value // 10) + (value % 10)
                total += value
            
            verification = 10 - (total % 10)
            return 0 if verification == 10 else verification
            
        elif third_digit == 6:
            # Private company algorithm (Módulo 11)
            coefficients = [3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(ruc[i]) * coefficients[i] for i in range(8))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
            
        elif third_digit == 9:
            # Foreign entity algorithm (Módulo 11)
            coefficients = [4, 3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(ruc[i]) * coefficients[i] for i in range(9))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        return -1
    
    def _assess_contract_capacity(self, ruc: str, amount: float) -> Dict[str, Any]:
        """Assess contractor capacity based on contract amount."""
        third_digit = int(ruc[2])
        capacity = {
            "contract_category": self._categorize_contract_amount(amount),
            "requires_additional_validation": False,
            "warnings": [],
            "recommendations": []
        }
        
        # Enhanced validation for large contracts
        if amount > self.contract_thresholds["large"]:
            capacity["requires_additional_validation"] = True
            capacity["warnings"].append(f"Contrato de gran magnitud (${amount:,.2f}) requiere verificación exhaustiva")
            
            if third_digit not in [6, 9]:  # Not a company
                capacity["warnings"].append("Persona natural para contrato de gran magnitud - verificar capacidad")
        
        if amount > self.contract_thresholds["mega"]:
            capacity["warnings"].append("MEGA CONTRATO - Requiere validación especial de capacidad financiera")
            capacity["recommendations"].append("Solicitar estados financieros auditados")
            capacity["recommendations"].append("Verificar experiencia en proyectos similares")
        
        return capacity
    
    def _categorize_contract_amount(self, amount: float) -> str:
        """Categorize contract amount for assessment purposes."""
        if amount < self.contract_thresholds["small"]:
            return "small"
        elif amount < self.contract_thresholds["medium"]:
            return "medium"
        elif amount < self.contract_thresholds["large"]:
            return "large"
        else:
            return "mega"
    
    def _analyze_search_content_enhanced(self, search_results: str) -> Dict[str, List[str]]:
        """Enhanced analysis of search content with more sophisticated patterns."""
        content = search_results.lower()
        
        findings = {
            "positive_indicators": [],
            "warning_indicators": [],
            "risk_indicators": [],
            "neutral_information": [],
            "official_sources_found": []
        }
        
        # Enhanced positive indicators
        positive_patterns = [
            (r"(certificad[oa]|acreditad[oa])", "Empresa certificada o acreditada"),
            (r"(experiencia|trayectoria).{0,20}(años|proyectos)", "Empresa con experiencia comprobada"),
            (r"(obras?.{0,10}(entregad|finaliz|complet))", "Obras entregadas exitosamente"),
            (r"(iso\s*\d+|certificacion.{0,20}calidad)", "Certificaciones de calidad"),
            (r"(reconocimient|premio|galardon)", "Reconocimientos recibidos"),
            (r"(responsabilidad\s*social|sostenib)", "Enfoque en responsabilidad social"),
            (r"(personal\s*calificado|equipo\s*especializ)", "Personal especializado"),
            (r"(habilitad[oa].{0,10}sercop)", "Habilitado en SERCOP")
        ]
        
        for pattern, description in positive_patterns:
            if re.search(pattern, content):
                findings["positive_indicators"].append(description)
        
        # Enhanced risk indicators
        risk_patterns = [
            (r"(sancion|multad|penalizad)", "Sanciones o multas identificadas"),
            (r"(inhabilitad|suspend|clausurad)", "Inhabilitaciones o suspensiones"),
            (r"(incumplimient|abandon|paraliz)", "Incumplimientos contractuales"),
            (r"(demanda|juicio|proces.{0,10}legal)", "Procesos legales en curso"),
            (r"(fraud|corrupci|ilegal)", "Indicios de fraude o corrupción"),
            (r"(obras?.{0,10}(abandon|paraliz|inconclus))", "Obras abandonadas o paralizadas"),
            (r"(problem.{0,10}financier|insolvenc)", "Problemas financieros"),
            (r"(controversia|conflict|disputa)", "Controversias o conflictos")
        ]
        
        for pattern, description in risk_patterns:
            if re.search(pattern, content):
                findings["risk_indicators"].append(description)
        
        # Warning indicators (moderate concerns)
        warning_patterns = [
            (r"(empresa\s*nueva|recient.{0,10}creaci)", "Empresa de reciente creación"),
            (r"(experiencia\s*limitada|pocos?\s*proyectos)", "Experiencia limitada"),
            (r"(atrasos?\s*menores?|observaciones?)", "Atrasos menores u observaciones"),
            (r"(cambio.{0,10}directiv|nueva\s*administraci)", "Cambios en la dirección")
        ]
        
        for pattern, description in warning_patterns:
            if re.search(pattern, content):
                findings["warning_indicators"].append(description)
        
        # Extract neutral information
        neutral_patterns = [
            (r"(telefono|direccion|contacto)", "Información de contacto disponible"),
            (r"(años?.{0,10}(operaci|mercado|fundaci))", "Información sobre años de operación"),
            (r"(actividad\s*economica|giro\s*comercial)", "Actividad económica identificada"),
            (r"(representante\s*legal|gerente)", "Información de representación legal")
        ]
        
        for pattern, description in neutral_patterns:
            if re.search(pattern, content):
                findings["neutral_information"].append(description)
        
        return findings
    
    def _identify_official_sources(self, search_results: str) -> List[str]:
        """Identify official Ecuadorian sources in search results."""
        content = search_results.lower()
        found_sources = []
        
        source_patterns = {
            "sercop.gob.ec": "Portal Oficial de Compras Públicas",
            "sri.gob.ec": "Servicio de Rentas Internas",
            "supercias.gob.ec": "Superintendencia de Compañías",
            "compraspublicas.gob.ec": "Sistema de Contratación Pública",
            "funcionjudicial.gob.ec": "Función Judicial",
            "contraloria.gob.ec": "Contraloría General del Estado"
        }
        
        for source, description in source_patterns.items():
            if source in content:
                found_sources.append(f"{description} ({source})")
        
        return found_sources
    
    def _assess_information_quality(self, search_results: str) -> str:
        """Assess the quality of information found in search results."""
        if not search_results or len(search_results.strip()) < 100:
            return "insufficient"
        
        content = search_results.lower()
        
        # Check for official sources
        official_found = any(source in content for source in self.official_sources)
        
        # Check for substantial content
        substantial = len(search_results) > 1000
        
        # Check for specific information types
        has_contact_info = any(term in content for term in ["teléfono", "dirección", "contacto"])
        has_business_info = any(term in content for term in ["empresa", "sociedad", "negocio"])
        
        if official_found and substantial:
            return "excellent"
        elif official_found or (substantial and has_contact_info and has_business_info):
            return "good"
        elif substantial or has_business_info:
            return "acceptable"
        else:
            return "limited"
    
    def _calculate_enhanced_rating(self, findings: Dict, ruc_data: Dict, amount: float) -> str:
        """Calculate enhanced overall rating with multiple factors."""
        if not ruc_data.get("valid", False):
            return "rejected"
        
        positive_count = len(findings.get("positive_indicators", []))
        risk_count = len(findings.get("risk_indicators", []))
        warning_count = len(findings.get("warning_indicators", []))
        
        # Critical rejection criteria
        if risk_count > 3:
            return "rejected"
        
        # High risk criteria
        if risk_count > 1 or (risk_count > 0 and warning_count > 2):
            return "high_risk"
        
        # Moderate risk criteria  
        if risk_count > 0 or warning_count > 3:
            return "moderate_risk"
        
        # Positive assessment criteria
        if positive_count > 3 and warning_count <= 1:
            return "highly_recommended"
        elif positive_count > 1 and warning_count <= 2:
            return "recommended"
        elif positive_count > 0 or warning_count <= 1:
            return "acceptable"
        else:
            return "insufficient_information"
    
    def _assess_risk_level(self, findings: Dict) -> str:
        """Assess overall risk level based on findings."""
        risk_count = len(findings.get("risk_indicators", []))
        warning_count = len(findings.get("warning_indicators", []))
        
        if risk_count > 2:
            return "critical"
        elif risk_count > 0:
            return "high"
        elif warning_count > 2:
            return "medium"
        elif warning_count > 0:
            return "low"
        else:
            return "minimal"
    
    def _generate_enhanced_recommendations(self, assessment: Dict) -> List[str]:
        """Generate enhanced actionable recommendations."""
        recommendations = []
        rating = assessment.get("contractor_intelligence", {}).get("overall_rating", "")
        risk_level = assessment.get("contractor_intelligence", {}).get("risk_level", "")
        findings = assessment.get("detailed_findings", {})
        
        # Critical and high-risk cases
        if rating == "rejected":
            recommendations.extend([
                "🔴 RECHAZAR - No cumple requisitos mínimos",
                "No proceder con evaluación técnica",
                "Documentar razones del rechazo"
            ])
        elif rating == "high_risk":
            recommendations.extend([
                "⚠️ ALTO RIESGO - Proceder con extrema cautela",
                "Solicitar garantías adicionales (mínimo 15% del contrato)",
                "Implementar supervisión intensiva",
                "Verificar antecedentes con SERCOP directamente"
            ])
        elif rating == "moderate_risk":
            recommendations.extend([
                "🟡 RIESGO MODERADO - Verificación adicional requerida",
                "Solicitar aclaraciones sobre observaciones identificadas",
                "Incrementar garantías de cumplimiento (10% del contrato)",
                "Establecer hitos de control más frecuentes"
            ])
        elif rating in ["recommended", "highly_recommended"]:
            recommendations.extend([
                "🟢 CONTRATISTA ACEPTABLE - Proceder con condiciones estándar",
                "Aplicar garantías normativas (5% fiel cumplimiento)",
                "Supervisión técnica estándar"
            ])
        else:
            recommendations.extend([
                "❓ INFORMACIÓN INSUFICIENTE - Requiere verificación manual",
                "Solicitar documentación adicional",
                "Verificar con fuentes oficiales directamente"
            ])
        
        # Add specific recommendations based on findings
        risk_indicators = findings.get("risk_indicators", [])
        if risk_indicators:
            recommendations.append("Investigar específicamente: " + "; ".join(risk_indicators[:3]))
        
        return recommendations
    
    def _define_verification_steps(self, assessment: Dict) -> List[str]:
        """Define specific next steps for verification."""
        rating = assessment.get("contractor_intelligence", {}).get("overall_rating", "")
        
        steps_map = {
            "rejected": [
                "Notificar inmediatamente el rechazo",
                "Proceder con siguiente oferente calificado"
            ],
            "high_risk": [
                "Solicitar información adicional en 48 horas",
                "Verificar con SERCOP estado actual",
                "Consultar referencias de contratos anteriores"
            ],
            "moderate_risk": [
                "Solicitar aclaraciones en 72 horas",
                "Verificar experiencia específica en proyectos similares",
                "Evaluar capacidad financiera actual"
            ],
            "recommended": [
                "Proceder con evaluación técnica",
                "Verificar documentación legal estándar",
                "Confirmar garantías requeridas"
            ],
            "highly_recommended": [
                "Proceder con evaluación acelerada",
                "Preparar documentación contractual"
            ]
        }
        
        return steps_map.get(rating, [
            "Realizar verificación manual completa",
            "Solicitar información faltante",
            "Re-evaluar en 5 días hábiles"
        ])
    
    def _make_final_decision(self, ruc_data: Dict, analysis_data: Dict) -> Dict[str, Any]:
        """Make final decision with clear justification."""
        if not ruc_data.get("valid", False):
            return {
                "decision": "RECHAZAR",
                "justification": "RUC inválido - no cumple requisitos técnicos básicos",
                "confidence": "alta",
                "requires_approval": False
            }
        
        rating = analysis_data.get("contractor_intelligence", {}).get("overall_rating", "")
        risk_level = analysis_data.get("contractor_intelligence", {}).get("risk_level", "")
        
        decision_matrix = {
            "rejected": ("RECHAZAR", "No cumple criterios mínimos de elegibilidad", "alta", False),
            "high_risk": ("RECHAZAR CON OPCIÓN DE SUBSANACIÓN", "Alto riesgo identificado", "alta", True),
            "moderate_risk": ("APROBAR CON CONDICIONES", "Riesgo moderado manejable", "media", True),
            "recommended": ("APROBAR", "Contratista calificado", "alta", False),
            "highly_recommended": ("APROBAR PREFERENTE", "Contratista altamente calificado", "alta", False)
        }
        
        decision, justification, confidence, requires_approval = decision_matrix.get(
            rating, ("REVISAR MANUALMENTE", "Evaluación inconclusa", "baja", True)
        )
        
        return {
            "decision": decision,
            "justification": justification,
            "confidence": confidence,
            "requires_approval": requires_approval,
            "risk_level": risk_level
        }
    
    def _generate_validation_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate specific recommendations based on validation results."""
        recommendations = []
        
        if not validation_result.get("valid", False):
            recommendations.append("ACCIÓN INMEDIATA: Rechazar por RUC inválido")
            recommendations.append("Solicitar corrección de información")
            return recommendations
        
        if not validation_result.get("eligible_for_contracts", False):
            recommendations.append("ADVERTENCIA: Verificar elegibilidad para contratos públicos")
        
        warnings = validation_result.get("warnings", [])
        if warnings:
            recommendations.append("Revisar advertencias identificadas:")
            recommendations.extend([f"• {w}" for w in warnings])
        
        amount = validation_result.get("contract_amount", 0)
        if amount > self.contract_thresholds["large"]:
            recommendations.append("Contrato de gran magnitud - verificación exhaustiva requerida")
        
        return recommendations if recommendations else ["RUC válido - proceder con verificación estándar"]
    
    # Additional helper methods for comprehensive reporting
    
    def _determine_final_status(self, ruc_data: Dict, analysis_data: Dict) -> str:
        """Determine final verification status."""
        if not ruc_data.get("valid", False):
            return "REJECTED_INVALID_RUC"
        
        rating = analysis_data.get("contractor_intelligence", {}).get("overall_rating", "")
        
        status_map = {
            "rejected": "REJECTED_RISK_FACTORS",
            "high_risk": "CONDITIONAL_HIGH_RISK",
            "moderate_risk": "CONDITIONAL_MODERATE_RISK",
            "recommended": "APPROVED_QUALIFIED",
            "highly_recommended": "APPROVED_HIGHLY_QUALIFIED"
        }
        
        return status_map.get(rating, "PENDING_MANUAL_REVIEW")
    
    def _generate_executive_recommendation(self, ruc_data: Dict, analysis_data: Dict) -> Dict[str, str]:
        """Generate executive-level recommendation."""
        rating = analysis_data.get("contractor_intelligence", {}).get("overall_rating", "unknown")
        
        exec_recommendations = {
            "rejected": {
                "action": "NO ADJUDICAR",
                "reason": "Contratista no cumple requisitos mínimos",
                "priority": "INMEDIATA"
            },
            "high_risk": {
                "action": "ADJUDICAR CON RESERVAS",
                "reason": "Requiere garantías adicionales y supervisión intensiva",
                "priority": "ALTA"
            },
            "moderate_risk": {
                "action": "ADJUDICAR CON CONDICIONES",
                "reason": "Aplicar medidas de mitigación de riesgo",
                "priority": "MEDIA"
            },
            "recommended": {
                "action": "ADJUDICAR",
                "reason": "Contratista calificado para el proyecto",
                "priority": "NORMAL"
            },
            "highly_recommended": {
                "action": "ADJUDICAR PREFERENTE",
                "reason": "Contratista altamente calificado",
                "priority": "NORMAL"
            }
        }
        
        return exec_recommendations.get(rating, {
            "action": "REVISAR MANUALMENTE",
            "reason": "Evaluación requiere revisión adicional",
            "priority": "ALTA"
        })
    
    def _extract_key_findings(self, analysis_data: Dict) -> List[str]:
        """Extract key findings for executive summary."""
        findings = analysis_data.get("detailed_findings", {})
        key_findings = []
        
        positive = findings.get("positive_indicators", [])
        risks = findings.get("risk_indicators", [])
        warnings = findings.get("warning_indicators", [])
        
        if positive:
            key_findings.append(f"✅ {len(positive)} indicadores positivos identificados")
        
        if risks:
            key_findings.append(f"⚠️ {len(risks)} factores de riesgo detectados")
        
        if warnings:
            key_findings.append(f"🟡 {len(warnings)} señales de advertencia")
        
        official_sources = findings.get("official_sources_found", [])
        if official_sources:
            key_findings.append(f"📊 Verificado con {len(official_sources)} fuentes oficiales")
        
        return key_findings
    
    def _identify_critical_issues(self, analysis_data: Dict) -> List[str]:
        """Identify critical issues requiring immediate attention."""
        findings = analysis_data.get("detailed_findings", {})
        risk_indicators = findings.get("risk_indicators", [])
        
        # Filter for critical issues
        critical_keywords = ["sanción", "inhabilitad", "fraud", "incumplimiento", "demanda"]
        critical_issues = []
        
        for risk in risk_indicators:
            if any(keyword in risk.lower() for keyword in critical_keywords):
                critical_issues.append(risk)
        
        return critical_issues[:5]  # Limit to top 5 critical issues
    
    def _create_implementation_plan(self, ruc_data: Dict, analysis_data: Dict) -> Dict[str, List[str]]:
        """Create implementation plan based on assessment."""
        rating = analysis_data.get("contractor_intelligence", {}).get("overall_rating", "")
        
        plans = {
            "high_risk": {
                "immediate": ["Solicitar garantías adicionales", "Establecer supervisión diaria"],
                "short_term": ["Verificar cumplimiento semanal", "Auditorías sorpresa"],
                "ongoing": ["Monitoreo continuo", "Revisión mensual de avances"]
            },
            "moderate_risk": {
                "immediate": ["Confirmar garantías estándar", "Establecer supervisión regular"],
                "short_term": ["Verificar cumplimiento quincenal", "Inspecciones programadas"],
                "ongoing": ["Monitoreo estándar", "Revisión mensual"]
            },
            "recommended": {
                "immediate": ["Proceder con adjudicación estándar"],
                "short_term": ["Supervisión técnica normal"],
                "ongoing": ["Seguimiento contractual estándar"]
            }
        }
        
        return plans.get(rating, {
            "immediate": ["Evaluación manual requerida"],
            "short_term": ["Definir medidas específicas"],
            "ongoing": ["Plan por definir"]
        })
    
    def _define_monitoring_requirements(self, analysis_data: Dict) -> Dict[str, Any]:
        """Define monitoring requirements based on risk assessment."""
        risk_level = analysis_data.get("contractor_intelligence", {}).get("risk_level", "unknown")
        
        monitoring_map = {
            "critical": {
                "frequency": "Diaria",
                "reports": "Diarios con alertas inmediatas",
                "inspections": "Sorpresa y programadas",
                "escalation": "Inmediata a nivel directivo"
            },
            "high": {
                "frequency": "Semanal",
                "reports": "Semanales con alertas",
                "inspections": "Bi-semanales",
                "escalation": "48 horas a supervisión"
            },
            "medium": {
                "frequency": "Quincenal",
                "reports": "Quincenales",
                "inspections": "Mensuales",
                "escalation": "Una semana a coordinación"
            },
            "low": {
                "frequency": "Mensual",
                "reports": "Mensuales estándar",
                "inspections": "Trimestrales",
                "escalation": "Según procedimiento estándar"
            }
        }
        
        return monitoring_map.get(risk_level, {
            "frequency": "Por definir",
            "reports": "Según evaluación manual",
            "inspections": "Por definir",
            "escalation": "Manual"
        })