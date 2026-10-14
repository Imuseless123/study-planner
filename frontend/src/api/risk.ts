import { api } from './client';

export interface RiskComponents {
  sleep_deficit: number;
  workload_density: number;
  deadline_proximity: number;
  study_inconsistency: number;
}

export interface RiskWeights {
  sleep_deficit: number;
  workload_density: number;
  deadline_proximity: number;
  study_inconsistency: number;
}

export interface RiskScore {
  risk_score: number;
  level: 'low' | 'moderate' | 'high';
  components: RiskComponents;
  weights: RiskWeights;
  disclaimer: string;
}

export const riskApi = {
  getScore: () =>
    api.get<RiskScore>('/api/risk/score').then((r) => r.data),
};
