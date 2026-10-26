import { useEffect, useState } from 'react';

/**
 * Responsive hook — returns true when viewport < breakpoint.
 * Default 768px (Ant Design's `md` breakpoint).
 */
export function useIsMobile(breakpoint: number = 768): boolean {
  const [isMobile, setIsMobile] = useState<boolean>(
    typeof window !== 'undefined' && window.innerWidth < breakpoint
  );

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < breakpoint);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, [breakpoint]);

  return isMobile;
}
