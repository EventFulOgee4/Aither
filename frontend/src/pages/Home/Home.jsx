import React from "react";
import "./home.css";
import Sidebar from "../../components/Sidebar/Sidebar";
import Topbar from "../../components/Topbar/Topbar";
import OrbLogo from "../../components/OrbLogo/OrbLogo";
import PromptCard from "../../components/PromptCard/PromptCard";
import ExampleCards from "../../components/ExampleCards/ExampleCards";

export default function Home() {
  return (
    <div className="home-root">
      <Sidebar />
      <div className="home-main">
        <Topbar />
        <main className="home-content">
          <OrbLogo />
          <h1 className="headline">you feeling today?</h1>

          <PromptCard />

          <div className="examples-label">
            ASK AITHER ONE OF THE EXAMPLES BELOW
          </div>
          <ExampleCards />
        </main>
      </div>
    </div>
  );
}
