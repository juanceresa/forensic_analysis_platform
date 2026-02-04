'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useInView, useMotionValue, useSpring } from 'framer-motion';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  delay?: number;
  className?: string;
  formatOptions?: Intl.NumberFormatOptions;
}

export function AnimatedNumber({
  value,
  duration = 0.6,
  delay = 0,
  className = '',
  formatOptions,
}: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const [displayValue, setDisplayValue] = useState(0);

  // Check for reduced motion preference
  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, {
    duration: duration * 1000,
    bounce: 0,
  });

  useEffect(() => {
    if (prefersReducedMotion) {
      setDisplayValue(value);
      return;
    }

    if (isInView) {
      const timeout = setTimeout(() => {
        motionValue.set(value);
      }, delay * 1000);

      return () => clearTimeout(timeout);
    }
  }, [isInView, value, motionValue, delay, prefersReducedMotion]);

  useEffect(() => {
    if (prefersReducedMotion) return;

    const unsubscribe = springValue.on('change', (latest) => {
      setDisplayValue(Math.round(latest));
    });

    return () => unsubscribe();
  }, [springValue, prefersReducedMotion]);

  const formattedValue = formatOptions
    ? new Intl.NumberFormat('en-US', formatOptions).format(displayValue)
    : displayValue.toLocaleString();

  return (
    <motion.span
      ref={ref}
      className={`tabular-nums ${className}`}
      initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.3, delay }}
    >
      {formattedValue}
    </motion.span>
  );
}
