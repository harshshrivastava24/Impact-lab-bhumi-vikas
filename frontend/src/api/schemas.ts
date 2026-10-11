import { z } from 'zod';

/*
 * Zod schemas for the API contract in master-prompt/00_SHARED_CONTEXT.md.
 * Every response is parsed with these before use; TS types come from z.infer.
 *
 * Contract additions (documented in the shared context):
 *  - Figure.warning: Rule 53(1)(i) development-type warning (FR-16).
 *  - LookupRequest.query_text: free text for backend keyword fallback and
 *    not-found (FR-12, FR-26) when no topic or parameters were parsed.
 *  - PlanCheckRequest.resolution: FR-39 "use_dimensions" resolution.
 */

export const LanguageSchema = z.enum(['en', 'hi']);
export type Language = z.infer<typeof LanguageSchema>;

export const UseTypeSchema = z.enum(['residential', 'commercial', 'public', 'industrial', 'agricultural']);
export type UseType = z.infer<typeof UseTypeSchema>;

export const DevelopmentTypeSchema = z.enum(['detached', 'semi_detached', 'row']);
export type DevelopmentType = z.infer<typeof DevelopmentTypeSchema>;

export const TOPICS = [
  'front_setback',
  'rear_setback',
  'side_setback',
  'height_limit',
  'far',
  'ground_coverage',
  'application_fee',
  'permission_fee',
  'permission_validity',
  'documents_required',
  'plan_check',
] as const;
export const TopicSchema = z.enum(TOPICS);
export type Topic = z.infer<typeof TopicSchema>;

export const FEE_TOPICS: readonly Topic[] = ['application_fee', 'permission_fee'];

export const ParamsSchema = z.object({
  plot_area: z.number(),
  road_width: z.number(),
  use_type: UseTypeSchema,
  built_up_area: z.number().optional(),
  height: z.number().optional(),
  development_type: DevelopmentTypeSchema.optional(),
  frontage: z.number().optional(),
  depth: z.number().optional(),
  floor_to_floor: z.number().optional(),
  existing_developed_area: z.boolean().optional(),
  streets_abutting: z.union([z.literal(1), z.literal(2)]).optional(),
});
export type Params = z.infer<typeof ParamsSchema>;

export const ParseResponseSchema = z.object({
  language: LanguageSchema,
  params: ParamsSchema.partial(),
  topics: z.array(TopicSchema),
  used_inference: z.boolean(),
});
export type ParseResponse = z.infer<typeof ParseResponseSchema>;

const BaseFigureSchema = z.object({
  topic: TopicSchema,
  label: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  derived: z.boolean(),
  conditional: z.boolean(),
  trace: z.string(),
  rule: z.string(),
  page: z.number().int().positive(),
  warning: z.string().optional(),
});
export type Figure = z.infer<typeof BaseFigureSchema> & { cases?: Figure[] };
export const FigureSchema: z.ZodType<Figure> = BaseFigureSchema.extend({
  cases: z.lazy(() => z.array(FigureSchema)).optional(),
});

export const CitationSchema = z.object({
  rule: z.string(),
  sub_rule: z.string().optional(),
  title: z.string(),
  part: z.string(),
  page_start: z.number().int().positive(),
  page_end: z.number().int().positive(),
  text_en: z.string(),
  sub_rule_text_en: z.string().optional(),
  pdf_en_url: z.string(),
  pdf_hi_url: z.string(),
  footnotes: z.array(z.string()),
});
export type Citation = z.infer<typeof CitationSchema>;

export const AmendmentFlagSchema = z.object({
  date: z.string(),
  rule: z.string(),
  concerns: z.string(),
  source_url: z.string(),
  source_kind: z.enum(['primary', 'secondary']),
  applied: z.literal(false),
  note: z.string(),
});
export type AmendmentFlag = z.infer<typeof AmendmentFlagSchema>;

export const StatusSchema = z.enum(['answered', 'not_found', 'refused', 'blocked']);
export type Status = z.infer<typeof StatusSchema>;

export const ResolutionSchema = z.enum(['correct_inputs', 'use_dimensions']);
export type Resolution = z.infer<typeof ResolutionSchema>;

export const LookupResponseSchema = z.object({
  status: StatusSchema,
  message: z.string().optional(),
  resolutions: z.array(ResolutionSchema).optional(),
  figures: z.array(FigureSchema),
  citations: z.array(CitationSchema),
  version: z.object({ consolidated_to: z.string(), label: z.string() }),
  amendment_flags: z.array(AmendmentFlagSchema),
  disclaimer: z.string(),
  language: LanguageSchema,
  used_inference: z.boolean(),
});
export type LookupResponse = z.infer<typeof LookupResponseSchema>;

export const LookupRequestSchema = z.object({
  params: ParamsSchema.partial(),
  topics: z.array(TopicSchema),
  language: LanguageSchema,
  query_text: z.string().optional(),
});
export type LookupRequest = z.infer<typeof LookupRequestSchema>;

export const SideSchema = z.enum(['front', 'rear', 'left', 'right']);
export type Side = z.infer<typeof SideSchema>;

export const SideReqSchema = z.object({
  value: z.number(),
  rule: z.string(),
  sub_rule: z.string(),
  page: z.number().int().positive(),
  trace: z.string(),
});
export type SideReq = z.infer<typeof SideReqSchema>;

export const RectSchema = z.object({
  x: z.number(),
  y: z.number(),
  width: z.number(),
  depth: z.number(),
  area: z.number(),
});
export type Rect = z.infer<typeof RectSchema>;

export const SideRowSchema = z.object({
  side: SideSchema,
  required: z.number(),
  provided: z.number(),
  shortfall: z.number(),
  rule: z.string(),
  page: z.number().int().positive(),
  trace: z.string(),
});
export type SideRow = z.infer<typeof SideRowSchema>;

export const OverlapSchema = z.object({
  side: SideSchema,
  x: z.number(),
  y: z.number(),
  width: z.number(),
  depth: z.number(),
  shortfall: z.number(),
});
export type Overlap = z.infer<typeof OverlapSchema>;

export const PLAN_RESULT_CONFLICT = 'Setback conflict found';
export const PLAN_RESULT_CLEAR = 'No setback conflict found against the checks listed';

export const ExceptionSchema = z.object({
  id: z.string(),
  label: z.string(),
  rule: z.string(),
  page: z.number().int().positive(),
});
export type PlanException = z.infer<typeof ExceptionSchema>;

export const GeometrySchema = z.object({
  plot: z.object({ width: z.number(), depth: z.number(), area: z.number() }),
  required: z.object({ front: SideReqSchema, rear: SideReqSchema, left: SideReqSchema, right: SideReqSchema }),
  envelope: RectSchema,
  footprint: RectSchema,
  sides: z.array(SideRowSchema),
  overlaps: z.array(OverlapSchema),
  result: z.string(),
  result_kind: z.enum(['conflict', 'clear']),
  checks_performed: z.array(z.string()),
  not_checked: z.string(),
  ground_coverage_derived: z.number(),
  exceptions_available: z.array(ExceptionSchema),
});
export type Geometry = z.infer<typeof GeometrySchema>;

export const PlanCheckResponseSchema = LookupResponseSchema.extend({
  geometry: GeometrySchema.optional(),
});
export type PlanCheckResponse = z.infer<typeof PlanCheckResponseSchema>;

export const FootprintSchema = z.object({
  front: z.number(),
  rear: z.number(),
  left: z.number(),
  right: z.number(),
});
export type Footprint = z.infer<typeof FootprintSchema>;

export const PlanCheckRequestSchema = z.object({
  params: ParamsSchema,
  footprint: FootprintSchema,
  language: LanguageSchema,
  resolution: z.literal('use_dimensions').optional(),
});
export type PlanCheckRequest = z.infer<typeof PlanCheckRequestSchema>;

export const ErrorBodySchema = z.object({ detail: z.string() });
