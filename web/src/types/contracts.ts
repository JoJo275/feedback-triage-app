import type { components } from "./openapi.generated";

type Schemas = components["schemas"];

export type UserRole = Schemas["UserRole"];
export type WorkspaceRole = Schemas["WorkspaceRole"];
export type FeedbackStatus = Schemas["Status"];
export type FeedbackSource = Schemas["Source"];

export type UserDto = Schemas["UserResponse"];
export type MembershipDto = Schemas["MembershipResponse"];
export type WorkspaceDto = Schemas["WorkspaceResponse"];
export type MeResponse = Schemas["MeResponse"];

export type FeedbackItemDto = Schemas["FeedbackResponseV2"];
export type FeedbackListEnvelope = Schemas["FeedbackListEnvelopeV2"];

export type DashboardCountsDto = Schemas["DashboardCountsResponse"];
export type DashboardIntakePointDto = Schemas["DashboardIntakePointResponse"];
export type DashboardTotalSignalsWidgetDto =
    Schemas["DashboardTotalSignalsWidgetResponse"];
export type DashboardDeltaDirection =
    DashboardTotalSignalsWidgetDto["delta_direction"];
export type DashboardSummaryDto = Schemas["DashboardSummaryResponse"];

export type SubmitterDto = Schemas["SubmitterResponse"];
export type SubmitterListEnvelope = Schemas["SubmitterListEnvelope"];

export type MemberUserDto = Schemas["MemberUserResponse"];
export type MemberDto = Schemas["MemberResponse"];
export type MemberListResponse = Schemas["MemberListResponse"];
