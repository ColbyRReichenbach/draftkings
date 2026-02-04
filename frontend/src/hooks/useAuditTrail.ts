import { useQuery } from '@tanstack/react-query';
import { riskClient } from '../api/riskClient';

export const useAuditTrail = () =>
  useQuery({
    queryKey: ['audit-trail'],
    queryFn: () => riskClient.getAuditTrail()
  });
