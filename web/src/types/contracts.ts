export type ExtensibleString<T extends string> = T | (string & {});

export type UserRole = ExtensibleString<"admin" | "team_member" | "demo">;
export type WorkspaceRole = ExtensibleString<"owner" | "team_member">;

export type FeedbackStatus = ExtensibleString<
    | "new"
    | "needs_info"
    | "reviewing"
    | "accepted"
    | "planned"
    | "in_progress"
    | "shipped"
    | "closed"
    | "spam"
    | "rejected"
>;

export type FeedbackSource = ExtensibleString<
    | "email"
    | "interview"
    | "reddit"
    | "support"
    | "app_store"
    | "twitter"
    | "web_form"
    | "other"
>;

export interface UserDto {
    id: string;
    email: string;
    is_verified: boolean;
    role: UserRole;
    theme_preference: string;
    created_at: string;
}

export interface MembershipDto {
    workspace_id: string;
    workspace_slug: string;
    workspace_name: string;
    role: WorkspaceRole;
}

export interface WorkspaceDto {
    id: string;
    slug: string;
    name: string;
    is_demo: boolean;
    public_submit_enabled: boolean;
    created_at: string;
}

export interface MeResponse {
    user: UserDto;
    memberships: MembershipDto[];
}

export interface FeedbackItemDto {
    id: number;
    workspace_id?: string;
    submitter_id?: string | null;
    assignee_user_id?: string | null;
    title: string;
    description: string | null;
    source: FeedbackSource;
    source_other?: string | null;
    type?: string;
    type_other?: string | null;
    priority?: string | null;
    pain_level: number;
    status: FeedbackStatus;
    published_to_roadmap?: boolean;
    published_to_changelog?: boolean;
    release_note?: string | null;
    created_at: string;
    updated_at: string;
}

export interface FeedbackListEnvelope {
    items: FeedbackItemDto[];
    total: number;
    skip: number;
    limit: number;
}

export interface DashboardCountsDto {
    total_signals: number;
    needs_action: number;
    high_pain_signals: number;
}

export interface DashboardIntakePointDto {
    day: string;
    received: number;
}

export type DashboardDeltaDirection = ExtensibleString<"up" | "down" | "flat">;

export interface DashboardTotalSignalsWidgetDto {
    widget_id: "kpi-total-signals";
    label: "Total signals";
    value: number;
    delta_pct: number;
    delta_direction: DashboardDeltaDirection;
    comparison_label: string;
    sparkline_points: number[];
    sparkline_date_labels: string[];
}

export interface DashboardSummaryDto {
    counts: DashboardCountsDto;
    intake_30d: DashboardIntakePointDto[];
    total_signals_widget: DashboardTotalSignalsWidgetDto;
}

export interface SubmitterDto {
    id: string;
    workspace_id: string;
    email: string | null;
    name: string | null;
    internal_notes: string | null;
    submission_count: number;
    first_seen_at: string;
    last_seen_at: string;
    created_at: string;
    updated_at: string;
}

export interface SubmitterListEnvelope {
    items: SubmitterDto[];
    total: number;
    skip: number;
    limit: number;
}

export interface MemberUserDto {
    id: string;
    email: string;
    role: UserRole;
    created_at: string;
}

export interface MemberDto {
    user: MemberUserDto;
    role: WorkspaceRole;
    joined_at: string;
}

export interface MemberListResponse {
    items: MemberDto[];
    total: number;
}
