import { Target, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface Props {
  value: string;
  onChange: (val: string) => void;
}

const StrategySelector = ({ value, onChange }: Props) => {
  const modes = [
    {
      id: "1",
      name: "Orgânico",
      icon: Target,
    },
    {
      id: "2",
      name: "Agressivo",
      icon: Zap,
    },
  ];

  return (
    <div className="segmented-control">
      {modes.map((mode) => {
        const isActive = value === mode.id;
        return (
          <button
            key={mode.id}
            onClick={() => onChange(mode.id)}
            className={`segmented-item ${isActive ? "segmented-item-active" : "segmented-item-inactive"}`}
          >
            <mode.icon className="w-3.5 h-3.5" />
            <span>{mode.name}</span>
          </button>
        );
      })}
    </div>
  );
};

export default StrategySelector;
