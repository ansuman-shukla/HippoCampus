import '../index.css';

interface Props {
    handle: () => void;
    text: string;
    textColor: string; 
    iSdisabled ?: boolean;
    IncMinWidth?:string;
  }
  
  export default function Button({ handle, text, textColor, iSdisabled,IncMinWidth }: Props) {

    return (
      <button
        type="button"
        onClick={handle}
        style={{color:`var(${textColor})`, minWidth: IncMinWidth ? `${IncMinWidth}`: '118px'}}
        className={`bg-black px-6 py-3 rounded-full 
                    hover:bg-transparent hover:text-black transition-colors
                    inter-500 text-xs border border-black tracking-wider`}
        onMouseEnter={(e) => (e.currentTarget.style.color = "black")}
        onMouseLeave={(e) => (e.currentTarget.style.color = `var(${textColor})`)}
        disabled={iSdisabled}
        
      >
        {iSdisabled ? '' : text}
      </button>
    );
  }
  