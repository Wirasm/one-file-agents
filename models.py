from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    documentType: str = Field(..., description="E.g., PolicyDocument, Amendment, Invoice, Mandate")
    documentDate: Optional[str] = Field(None, description="Issue date (YYYY-MM-DD)")
    pageCount: Optional[int] = Field(None, description="Total page count")
    originalReference: Optional[str] = Field(None, description="Original document reference (if any)")
    version: Optional[str] = Field(None, description="Version information")
    language: Optional[str] = Field(None, description="Language code")

class ContactInfo(BaseModel):
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class Issuer(BaseModel):
    name: str
    address: str
    contact: ContactInfo
    companyRegistration: Optional[str] = None

class InsuredParty(BaseModel):
    type: str = Field(..., description="Company or Individual")
    name: str
    address: str
    contact: ContactInfo
    representative: Optional[Dict[str, str]] = Field(
        None, description="E.g., { 'name': '...', 'role': '...' }"
    )

class Broker(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[ContactInfo] = None
    registrationDetails: Optional[str] = None

class CoveragePeriod(BaseModel):
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class RenewalInfo(BaseModel):
    automatic: Optional[bool] = None
    noticePeriod: Optional[str] = None

class Endorsement(BaseModel):
    type: Optional[str] = None
    reason: Optional[str] = None
    effectiveDate: Optional[str] = None

class Cancellation(BaseModel):
    cancellationTerms: Optional[str] = None
    widerrufsrecht: Optional[str] = None

class PolicyDetails(BaseModel):
    policyNumber: Optional[str] = None
    customerNumber: Optional[str] = None
    productType: Optional[str] = None
    coveragePeriod: Optional[CoveragePeriod] = None
    renewal: Optional[RenewalInfo] = None
    endorsement: Optional[Endorsement] = None
    cancellation: Optional[Cancellation] = None

class BillingPeriod(BaseModel):
    from_date: Optional[str] = Field(None, alias="from", description="Billing start date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, alias="to", description="Billing end date (YYYY-MM-DD)")

class Amounts(BaseModel):
    netPremium: Optional[float] = None
    taxRate: Optional[float] = None
    taxAmount: Optional[float] = None
    grossPremium: Optional[float] = None

class PaymentInstructions(BaseModel):
    paymentMethod: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    mandateReference: Optional[str] = None
    giroCode: Optional[str] = None

class PremiumDetails(BaseModel):
    billing: Optional[BillingPeriod] = None
    amounts: Optional[Amounts] = None
    paymentInstructions: Optional[PaymentInstructions] = None

class InsuredPersonDetails(BaseModel):
    name: str
    dateOfBirth: Optional[str] = None
    profession: Optional[str] = None
    address: Optional[str] = None

class RiskCoverageDetails(BaseModel):
    invalidityBasicSum: Optional[float] = None
    fullInvaliditySum: Optional[float] = None
    monthlyAccidentPension: Optional[float] = None
    deathBenefit: Optional[float] = None
    additionalNotes: Optional[str] = None

class RiskPremium(BaseModel):
    grossPremium: Optional[float] = None
    netPremium: Optional[float] = None
    taxAmount: Optional[float] = None
    taxRate: Optional[float] = None

class InsuredRisk(BaseModel):
    riskNumber: str
    insuredPerson: InsuredPersonDetails
    coverageDetails: RiskCoverageDetails
    premium: RiskPremium

class GeneralCoverage(BaseModel):
    coverageType: Optional[str] = Field(None, description="E.g., 'Unfallversicherung' or 'Sachversicherung'")
    insuredRisks: List[InsuredRisk] = Field(default_factory=list)

class GroupInsuredPerson(BaseModel):
    name: str
    dateOfBirth: Optional[str] = None
    beneficiaries: Optional[str] = None

class GroupCoverageDetails(BaseModel):
    invalidityBasicSum: Optional[float] = None
    fullInvaliditySum: Optional[float] = None
    monthlyAccidentPension: Optional[float] = None
    pensionType: Optional[str] = None
    deathBenefit: Optional[float] = None
    cosmeticOperationCoverage: Optional[float] = None
    rescueCosts: Optional[Dict[str, Any]] = None

class GroupPremium(BaseModel):
    perPerson: Optional[float] = None
    groupPremium: Optional[float] = None

class GroupCoverage(BaseModel):
    groupName: str
    insuredPersons: List[GroupInsuredPerson] = Field(default_factory=list)
    coverageDetails: GroupCoverageDetails
    premium: GroupPremium

class InsuredValue(BaseModel):
    description: str
    newValue: Optional[float] = None
    wertzuschlag: Optional[float] = None
    insuranceSum: Optional[float] = None
    priceBasis: Optional[str] = None

class PropertyInsurance(BaseModel):
    insuredValues: List[InsuredValue] = Field(default_factory=list)
    insuredHazards: List[str] = Field(default_factory=list)
    coverageExtensions: Optional[List[Dict[str, str]]] = None

class AdditionalInfo(BaseModel):
    notes: Optional[str] = None
    legalInformation: Optional[str] = None

class CoverageDetails(BaseModel):
    general: Optional[GeneralCoverage] = None
    group: Optional[GroupCoverage] = None
    risk: Optional[RiskCoverageDetails] = None

class APICallMetadata(BaseModel):
    cost: float = Field(0.0, description="Cost of the API call in USD")
    prompt_tokens: int = Field(0, description="Number of input tokens used")
    completion_tokens: int = Field(0, description="Number of output tokens used")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp of the API call")

class ExtractionResult(BaseModel):
    documentMetadata: DocumentMetadata
    issuer: Issuer
    insuredParty: InsuredParty
    broker: Optional[Broker] = None
    policyDetails: PolicyDetails
    premiumDetails: PremiumDetails
    coverage: CoverageDetails
    additionalInfo: Optional[AdditionalInfo] = None
    api_call_metadata: List[APICallMetadata] = Field(default_factory=list, description="Metadata for each API call")
    total_cost: float = Field(0.0, description="Total cost of all API calls in USD")

class ValidationIssue(BaseModel):
    section: str = Field(..., description="Which section has the issue (e.g., 'issuer', 'insuredParty', etc.)")
    issue: str = Field(..., description="A description of the discrepancy")
    recommendation: str = Field(..., description="A recommendation on how to correct the issue")

class ValidationReport(BaseModel):
    valid: bool = Field(..., description="Indicates whether the extraction is valid")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of issues found during validation")
