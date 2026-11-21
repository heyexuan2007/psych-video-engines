import { Composition, Still } from "remotion";
import { CharSheet } from "./CharSheet";
import { Cover } from "./Cover";
import { MV } from "./MV";
import { PersonSheet } from "./PersonSheet";
import { StoryMV } from "./StoryMV";
import { DURATION, FPS } from "./lib/util";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="TianTianMV" component={MV} durationInFrames={Math.round(DURATION * FPS)} fps={FPS} width={1920} height={1080} />
      <Composition id="TianTianStory" component={StoryMV} durationInFrames={Math.round(DURATION * FPS)} fps={FPS} width={1920} height={1080} />
      <Still id="Cover4x3" component={Cover} width={1440} height={1080} defaultProps={{ portrait: false }} />
      <Still id="Cover3x4" component={Cover} width={1080} height={1440} defaultProps={{ portrait: true }} />
      <Still id="PersonSheet" component={PersonSheet} width={1920} height={1080} />
      <Still id="CharSheet" component={CharSheet} width={1920} height={1080} />
    </>
  );
};
