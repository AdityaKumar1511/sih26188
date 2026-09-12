'use client';

import React from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

// ============================================================================
// SCROLL REVEAL — Fades + slides an element when it enters the viewport
// ============================================================================

type Direction = 'up' | 'down' | 'left' | 'right';

interface ScrollRevealProps {
  children: React.ReactNode;
  direction?: Direction;
  delay?: number;
  duration?: number;
  distance?: number;
  once?: boolean;
  amount?: number;
  className?: string;
  blur?: boolean;
  scale?: number;
}

const directionOffset = (direction: Direction, distance: number) => {
  switch (direction) {
    case 'up': return { y: distance, x: 0 };
    case 'down': return { y: -distance, x: 0 };
    case 'left': return { y: 0, x: distance };
    case 'right': return { y: 0, x: -distance };
  }
};

export function ScrollReveal({
  children,
  direction = 'up',
  delay = 0,
  duration = 0.6,
  distance = 40,
  once = true,
  amount = 0.2,
  className = '',
  blur = false,
  scale,
}: ScrollRevealProps) {
  const offset = directionOffset(direction, distance);

  return (
    <motion.div
      initial={{
        opacity: 0,
        x: offset.x,
        y: offset.y,
        filter: blur ? 'blur(8px)' : 'blur(0px)',
        scale: scale ?? 1,
      }}
      whileInView={{
        opacity: 1,
        x: 0,
        y: 0,
        filter: 'blur(0px)',
        scale: 1,
      }}
      viewport={{ once, amount }}
      transition={{
        duration,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ============================================================================
// STAGGER CONTAINER + ITEM — Children cascade in one by one
// ============================================================================

interface StaggerContainerProps {
  children: React.ReactNode;
  stagger?: number;
  delay?: number;
  once?: boolean;
  amount?: number;
  className?: string;
}

export function StaggerContainer({
  children,
  stagger = 0.1,
  delay = 0,
  once = true,
  amount = 0.15,
  className = '',
}: StaggerContainerProps) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount }}
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            delayChildren: delay,
            staggerChildren: stagger,
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface StaggerItemProps {
  children: React.ReactNode;
  direction?: Direction;
  distance?: number;
  duration?: number;
  className?: string;
  scale?: number;
}

export function StaggerItem({
  children,
  direction = 'up',
  distance = 30,
  duration = 0.5,
  className = '',
  scale,
}: StaggerItemProps) {
  const offset = directionOffset(direction, distance);

  return (
    <motion.div
      variants={{
        hidden: {
          opacity: 0,
          x: offset.x,
          y: offset.y,
          scale: scale ?? 1,
        },
        visible: {
          opacity: 1,
          x: 0,
          y: 0,
          scale: 1,
          transition: {
            duration,
            ease: [0.16, 1, 0.3, 1],
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ============================================================================
// PARALLAX SECTION — Subtle scroll-speed offset for depth
// ============================================================================

interface ParallaxSectionProps {
  children: React.ReactNode;
  speed?: number;
  className?: string;
}

export function ParallaxSection({
  children,
  speed = 0.15,
  className = '',
}: ParallaxSectionProps) {
  const ref = React.useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  });
  const y = useTransform(scrollYProgress, [0, 1], [speed * 100, -speed * 100]);

  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
}
