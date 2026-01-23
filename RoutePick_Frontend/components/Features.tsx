import React from 'react';
import { Compass, Cpu, Map, Zap } from 'lucide-react';

interface FeatureCardProps {
  title: string;
  description: string;
  image: string;
  icon: React.ReactNode;
  large?: boolean;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ title, description, image, icon, large }) => (
  <div className={`group relative overflow-hidden rounded-2xl ${large ? 'col-span-1 md:col-span-2 aspect-[2/1]' : 'col-span-1 aspect-square'}`}>
    <img 
      src={image} 
      alt={title} 
      className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
    />
    <div className="absolute inset-0 bg-black/30 group-hover:bg-black/40 transition-colors duration-300" />
    
    <div className="absolute bottom-0 left-0 p-8 w-full">
      <div className="flex items-center justify-between">
        <div>
          <div className="mb-2 text-white/80">{icon}</div>
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">{title}</h3>
          <p className="text-white/80 text-sm md:text-base max-w-md opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300">
            {description}
          </p>
        </div>
        <div className="text-white text-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          +
        </div>
      </div>
    </div>
  </div>
);

const Features: React.FC = () => {
  return (
    <section className="py-24 px-6 md:px-12 bg-route-gray">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tighter mb-6">
            Smarter Systems. <br />
            <span className="font-serif italic">Smoother Journeys.</span>
          </h2>
          <span className="inline-block px-4 py-1 rounded-full border border-gray-300 text-xs uppercase tracking-widest bg-white">
            Technology
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard 
            title="Predictive Routing"
            description="Our AI anticipates traffic, weather, and crowd density to ensure you're always on the optimal path."
            image="https://picsum.photos/seed/road_winding/800/600"
            icon={<Compass className="w-6 h-6" />}
            large={true}
          />
          <FeatureCard 
            title="Smart Stays"
            description="Automatic booking of eco-friendly, high-comfort accommodations that match your style."
            image="https://picsum.photos/seed/hotel_luxury/600/600"
            icon={<Zap className="w-6 h-6" />}
          />
          <FeatureCard 
            title="Local Immersion"
            description="Connect with local guides and experiences often missed by standard travel agents."
            image="https://picsum.photos/seed/people_culture/600/600"
            icon={<Map className="w-6 h-6" />}
          />
          <FeatureCard 
            title="Real-time Adaptability"
            description="Change of plans? The system instantly re-optimizes your entire itinerary in seconds."
            image="https://picsum.photos/seed/tech_map/800/600"
            icon={<Cpu className="w-6 h-6" />}
            large={true}
          />
        </div>
      </div>
    </section>
  );
};

export default Features;