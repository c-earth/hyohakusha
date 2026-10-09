"""Draw a vector classroom figure of rover coordination, then save one PDF.

Run from the repository root. Output uses landscape A3 with native-point layout,
standard PDF fonts and no network, controller, or raw-data access. The figure
distinguishes deterministic implemented tools from planned offline agent roles.
"""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas


class WorkflowFigure:
    """Compose a two-panel decision and architecture figure in PDF points.

    Coordinates use a top-left origin. Colors identify coordination, acquisition,
    saved evidence and optional offline workers; dashed lines denote feedback.
    """

    def __init__(self, output):
        """Initialize the canvas and fixed landscape page geometry."""
        self.width, self.height = landscape(A3)
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.pdf = canvas.Canvas(str(self.output), pagesize=(self.width, self.height))
        self.pdf.setTitle('Rover exploration: decisions, agents and tools')
        self.pdf.setAuthor('hyohakusha project')
        self.ink = HexColor('#193047')
        self.muted = HexColor('#607386')
        self.blue = HexColor('#2364AA')
        self.teal = HexColor('#147D83')
        self.amber = HexColor('#A86B18')
        self.purple = HexColor('#7255A2')

    def text(self, x, y, text, size=11, color=None, bold=False):
        """Write a single baseline using points; text must fit its planned region."""
        self.pdf.setFillColor(color or self.ink)
        self.pdf.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        self.pdf.drawString(x, self.height-y, text)

    def box(self, x, y, width, height, title, lines=(), color=None, fill='#FFFFFF', tag=None):
        """Draw a rounded card with accent, title and explicit body lines."""
        color = color or self.blue
        self.pdf.setFillColor(HexColor(fill))
        self.pdf.setStrokeColor(HexColor('#D9E3EB'))
        self.pdf.setLineWidth(.8)
        self.pdf.roundRect(x, self.height-y-height, width, height, 9, fill=1, stroke=1)
        self.pdf.setFillColor(color)
        self.pdf.roundRect(x+1, self.height-y-height+1, 4, height-2, 2, fill=1, stroke=0)
        self.text(x+15, y+23, title, 12, color, True)
        for index, line in enumerate(lines):
            self.text(x+15, y+41+index*14, line, 9.6, self.muted)
        if tag:
            self.text(x+width-54, y+20, tag, 7.5, color, True)

    def arrow(self, points, color=None, dashed=False):
        """Draw an orthogonal polyline and arrowhead at the final point."""
        color = color or self.muted
        self.pdf.setStrokeColor(color)
        self.pdf.setFillColor(color)
        self.pdf.setLineWidth(1.3)
        self.pdf.setDash(4, 3) if dashed else self.pdf.setDash()
        path = self.pdf.beginPath()
        path.moveTo(points[0][0], self.height-points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, self.height-y)
        self.pdf.drawPath(path)
        self.pdf.setDash()
        x, y = points[-1]
        px, py = points[-2]
        if abs(x-px) > abs(y-py):
            sign = 1 if x > px else -1
            head = [(x, y), (x-sign*6, y-3), (x-sign*6, y+3)]
        else:
            sign = 1 if y > py else -1
            head = [(x, y), (x-3, y-sign*6), (x+3, y-sign*6)]
        path = self.pdf.beginPath()
        path.moveTo(head[0][0], self.height-head[0][1])
        for hx, hy in head[1:]:
            path.lineTo(hx, self.height-hy)
        path.close()
        self.pdf.drawPath(path, fill=1, stroke=0)

    def decision(self, x, y, width, height, title, subtitle):
        """Draw a centered diamond for a coordinator decision."""
        self.pdf.setFillColor(HexColor('#EAF2FB'))
        self.pdf.setStrokeColor(self.blue)
        path = self.pdf.beginPath()
        for index, (px, py) in enumerate([(x+width/2,y), (x+width,y+height/2),
                                        (x+width/2,y+height), (x,y+height/2)]):
            if index == 0:
                path.moveTo(px, self.height-py)
            else:
                path.lineTo(px, self.height-py)
        path.close()
        self.pdf.drawPath(path, fill=1, stroke=1)
        self.pdf.setFillColor(self.blue)
        self.pdf.setFont('Helvetica-Bold', 11)
        self.pdf.drawCentredString(x+width/2, self.height-y-height/2+3, title)
        self.pdf.setFont('Helvetica', 9)
        self.pdf.drawCentredString(x+width/2, self.height-y-height/2-11, subtitle)

    def draw(self):
        """Render the workflow, role/tool hierarchy, legend and limits on one page."""
        self.pdf.setFillColor(HexColor('#F5F8FB'))
        self.pdf.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.pdf.setFillColor(self.ink)
        self.pdf.rect(0, self.height-110, self.width, 110, fill=1, stroke=0)
        self.text(40, 35, 'HY O H A K U S H A  /  ELEGOO SMART ROBOT CAR V4.0', 9, HexColor('#A6C4DE'), True)
        self.text(40, 70, 'Explore first. Learn in parallel.', 28, white, True)
        self.text(40, 94, 'Codex-native agents and skills, explicit task state, deterministic acquisition', 12, HexColor('#D7E6F0'))

        self.text(40, 140, '01  THE EXPLORATION DECISION LOOP', 12, self.blue, True)
        self.text(565, 140, '02  AGENTS, TOOLS AND HARDWARE', 12, self.teal, True)
        self.pdf.setStrokeColor(HexColor('#D9E3EB'))
        self.pdf.line(540, self.height-160, 540, self.height-705)

        steps = [
            ('Read state; define the authorized round', ['Objective, area assumptions, caps, deadline, retries']),
            ('Establish fresh stopped evidence', ['Battery, camera, bias/rest and required clearance']),
            ('Freeze and reserve a useful-view plan', ['1-3 forward / left / right actions, PWM60 / T200 ms']),
            ('Acquire through one controller', ['Sequential pulses; timed camera + IMU observation']),
            ('Stop, disconnect and retain evidence', ['N100 attempt, socket close; preserve failed trials']),
            ('Review the saved segment', ['Completion, rest, cleanup, sensors and latest images']),
        ]
        ys = [164, 235, 306, 377, 448, 519]
        for index, ((title, lines), y) in enumerate(zip(steps, ys)):
            self.box(70, y, 310, 55, title, lines, self.blue if index < 3 else self.teal)
            if index < 5:
                self.arrow([(225,y+55),(225,ys[index+1])])
        self.decision(92, 594, 266, 64, 'More supported exploration?', 'Within objective, time and pulse limits')
        self.arrow([(225,574),(225,594)])
        self.arrow([(92,626),(49,626),(49,333),(70,333)], self.blue)
        self.text(49, 611, 'YES', 8, self.blue, True)
        self.arrow([(225,658),(225,675)])
        self.box(105,675,240,39,'Close out while stopped',(),self.blue,fill='#EAF2FB')
        self.text(233, 670, 'NO', 8, self.blue, True)
        self.box(401,448,115,115,'Fault / doubt', ['Stop and diagnose', 'Bounded recovery', 'when authorized;', 'otherwise ask help'],self.amber,fill='#FFF6E8')
        self.arrow([(380,546),(392,546),(392,500),(401,500)],self.amber)
        self.arrow([(458,448),(458,261),(380,261)],self.amber,dashed=True)
        self.text(393,588,'No blind replay.',9,self.amber,True)
        self.text(393,603,'Never relax gates',9,self.muted)
        self.text(393,617,'to force a result.',9,self.muted)

        # The right panel separates commands, hardware and saved-data feedback.
        self.box(565,164,583,52,'Scope + instructions + persistent project state',
                 ['User scope / AGENTS.md / .agents/skills / selected mission ledger'],self.blue)
        self.arrow([(856,216),(856,233)],self.blue)
        self.box(665,233,382,64,'Main coordinator',
                 ['Choose route/view, track overall budgets, prioritize backlog', 'Sole hardware decision maker; keep supported work moving'],self.blue,fill='#EAF2FB')
        self.arrow([(760,297),(760,318)],self.teal)
        self.arrow([(955,297),(955,308),(1026,308),(1026,318)],self.teal)
        self.box(565,318,370,64,'Bounded acquisition runtime',
                 ['run_exploration.ps1 -> CalibrationSession', 'TCP owner + MotionSampler: commands, sensors, stop'],self.teal,tag='LIVE')
        self.box(953,318,195,64,'HTTP camera worker',
                 ['TimedCameraRecorder', 'JPEGs only; no TCP control'],self.teal,tag='LIVE')
        self.arrow([(750,382),(750,404)],self.teal)
        self.arrow([(1050,382),(1050,404)],self.teal)
        self.box(565,404,370,56,'UNO: wheels, IMU and stopped sensors',
                 ['N4 motion / N100 stop; N1, N2, N3, N7, N8'],self.teal,fill='#EAF7F5')
        self.box(953,404,195,56,'ESP32 camera', ['/capture over HTTP'],self.teal,fill='#EAF7F5')
        self.arrow([(750,460),(750,476),(856,476),(856,491)],self.muted)
        self.arrow([(1050,460),(1050,476),(856,476)],self.muted)
        self.box(665,491,382,53,'Immutable saved evidence',
                 ['Events, trials, telemetry, JPEGs and source hashes'],self.muted,fill='#EDF1F5')
        self.arrow([(856,544),(856,561)])
        self.box(665,561,382,53,'Review evidence; update durable task state',
                 ['review_segment / workflow_state / session_brief'],self.muted,fill='#EDF1F5')
        self.arrow([(665,586),(550,586),(550,265),(665,265)],self.blue,dashed=True)
        self.text(568,574,'Evidence feedback',8,self.blue,True)
        for x,title,lines in [
            (565,'rover_map',['Landmarks, view links, revisits','Unknown space stays unknown']),
            (765,'rover_images',['Overlap, parallax, diagnostics','Optional useful-view requests']),
            (965,'rover_evidence',['Faults, timing, contradictions','Evidence IDs + uncertainty']),
        ]:
            self.arrow([(856,614),(856,624),(x+91,624),(x+91,642)],self.purple,dashed=True)
            self.box(x,642,183,69,title,lines,self.purple,fill='#F2EEFA')
        self.text(565,732,'.codex/agents/*.toml  /  Definitions validated; client loading remains unverified.',9,self.purple,True)
        self.text(565,748,'Requests enter the ledger. Generated memory is supplementary. No hooks installed.',9,self.muted)

        self.pdf.setFillColor(self.ink)
        self.pdf.roundRect(40, self.height-812, self.width-80, 45, 8, fill=1, stroke=0)
        self.text(55,785,'EVIDENCE & LIMITS',9,HexColor('#A6C4DE'),True)
        self.text(185,785,'43 saved trials support native response and later rest. Metric pose, stop distance and cliff avoidance remain unverified.',9,white)
        self.text(185,801,'Solid: execution / data. Dashed: feedback / specialists. Reservations track budgets; live launchers do not enforce the ledger.',9,HexColor('#D7E6F0'))
        self.pdf.save()
        return self.output


if __name__ == '__main__':
    print(WorkflowFigure('output/pdf/rover-exploration-workflow.pdf').draw().resolve())
