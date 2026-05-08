from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

Mode = Literal["classification", "regression"]


class FeatureInput(BaseModel):
    Name: str = ""
    ReleaseDate: date = date(2020, 1, 1)

    RequiredAge: Annotated[int, Field(ge=0, le=21)] = 0
    DemoCount: Annotated[int, Field(ge=0)] = 0
    DeveloperCount: Annotated[int, Field(ge=0)] = 1
    DLCCount: Annotated[int, Field(ge=0)] = 0
    Metacritic: Annotated[int, Field(ge=0, le=100)] = 0
    MovieCount: Annotated[int, Field(ge=0)] = 0
    PackageCount: Annotated[int, Field(ge=0)] = 1
    PublisherCount: Annotated[int, Field(ge=0)] = 1
    ScreenshotCount: Annotated[int, Field(ge=0)] = 0
    SteamSpyOwners: Annotated[int, Field(ge=0)] = 0
    SteamSpyOwnersVariance: Annotated[int, Field(ge=0)] = 0
    SteamSpyPlayersEstimate: Annotated[int, Field(ge=0)] = 0
    SteamSpyPlayersVariance: Annotated[int, Field(ge=0)] = 0
    AchievementCount: Annotated[int, Field(ge=0)] = 0
    AchievementHighlightedCount: Annotated[int, Field(ge=0)] = 0
    PriceInitial: Annotated[float, Field(ge=0)] = 9.99
    PriceFinal: Annotated[float, Field(ge=0)] = 9.99
    ReleaseYear: Annotated[int, Field(ge=2003, le=2030)] = 2020
    ReleaseMonth: Annotated[int, Field(ge=1, le=12)] = 6

    ControllerSupport: bool = False
    IsFree: bool = False
    FreeVerAvail: bool = False
    PurchaseAvail: bool = True
    SubscriptionAvail: bool = False
    PlatformWindows: bool = True
    PlatformLinux: bool = False
    PlatformMac: bool = False
    PCReqsHaveMin: bool = False
    PCReqsHaveRec: bool = False
    LinuxReqsHaveMin: bool = False
    LinuxReqsHaveRec: bool = False
    MacReqsHaveMin: bool = False
    MacReqsHaveRec: bool = False
    CategorySinglePlayer: bool = True
    CategoryMultiplayer: bool = False
    CategoryCoop: bool = False
    CategoryMMO: bool = False
    CategoryInAppPurchase: bool = False
    CategoryIncludeSrcSDK: bool = False
    CategoryIncludeLevelEditor: bool = False
    CategoryVRSupport: bool = False
    GenreIsNonGame: bool = False
    GenreIsIndie: bool = False
    GenreIsAction: bool = False
    GenreIsAdventure: bool = False
    GenreIsCasual: bool = False
    GenreIsStrategy: bool = False
    GenreIsRPG: bool = False
    GenreIsSimulation: bool = False
    GenreIsEarlyAccess: bool = False
    GenreIsFreeToPlay: bool = False
    GenreIsSports: bool = False
    GenreIsRacing: bool = False
    GenreIsMassivelyMultiplayer: bool = False
    PriceCurrency: str = "USD"
    SupportEmail: str = ""
    SupportURL: str = ""
    AboutText: str = ""
    Background: str = ""
    ShortDescrip: str = ""
    DetailedDescrip: str = ""
    DRMNotice: str = ""
    ExtUserAcctNotice: str = ""
    HeaderImage: str = ""
    LegalNotice: str = ""
    Reviews: str = ""
    SupportedLanguages: str = ""
    Website: str = ""
    PCMinReqsText: str = ""
    PCRecReqsText: str = ""
    LinuxMinReqsText: str = ""
    LinuxRecReqsText: str = ""
    MacMinReqsText: str = ""
    MacRecReqsText: str = ""

    @model_validator(mode="after")
    def price_final_lte_initial(self) -> "FeatureInput":
        if self.PriceFinal > self.PriceInitial:
            raise ValueError("PriceFinal cannot exceed PriceInitial")
        return self


class PredictRequest(BaseModel):
    mode: Mode
    features: FeatureInput


class WhatIfRequest(BaseModel):
    mode: Mode
    base_features: FeatureInput
    modified_features: dict[str, int | float | bool | str | date]
