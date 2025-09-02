/* Demo Component - Showcase Design System */
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
} from "../ui/shared";

export function DesignSystemDemo() {
  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="heading-1 mb-2">Design System Demo</h1>
        <p className="body-large text-secondary">
          Showcase of the new modular design system components
        </p>
      </div>

      {/* Typography Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Typography</CardTitle>
          <CardDescription>
            Consistent typography scale with semantic classes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h1 className="heading-1">Heading 1</h1>
            <h2 className="heading-2">Heading 2</h2>
            <h3 className="heading-3">Heading 3</h3>
            <h4 className="heading-4">Heading 4</h4>
            <h5 className="heading-5">Heading 5</h5>
            <h6 className="heading-6">Heading 6</h6>
          </div>
          <div>
            <p className="body-large">
              Large body text with relaxed line height
            </p>
            <p className="body-base">Standard body text for most content</p>
            <p className="body-small">
              Small body text for secondary information
            </p>
            <p className="caption">Caption text for labels and metadata</p>
          </div>
        </CardContent>
      </Card>

      {/* Buttons Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Buttons</CardTitle>
          <CardDescription>Various button styles and states</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3 mb-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
          </div>
          <div className="flex flex-wrap gap-3 mb-4">
            <Button variant="success">Success</Button>
            <Button variant="warning">Warning</Button>
            <Button variant="error">Error</Button>
          </div>
          <div className="flex flex-wrap gap-3 mb-4">
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
            <Button size="icon">🔍</Button>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button loading>Loading</Button>
            <Button disabled>Disabled</Button>
          </div>
        </CardContent>
      </Card>

      {/* Inputs Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Form Controls</CardTitle>
          <CardDescription>
            Input fields with labels and validation states
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input label="Name" placeholder="Enter your name" required />
          <Input
            label="Email"
            type="email"
            placeholder="Enter your email"
            helperText="We'll never share your email"
          />
          <Input
            label="Error Example"
            placeholder="This field has an error"
            error
            helperText="This field is required"
          />
        </CardContent>
      </Card>

      {/* Badges Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Badges</CardTitle>
          <CardDescription>Status indicators and labels</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Badge variant="primary">Primary</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="error">Error</Badge>
            <Badge variant="neutral">Neutral</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Colors Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Colors</CardTitle>
          <CardDescription>Design system color palette</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div
                className="w-full h-16 rounded-lg mb-2"
                style={{ backgroundColor: "var(--color-primary-600)" }}
              ></div>
              <p className="caption">Primary</p>
            </div>
            <div className="text-center">
              <div
                className="w-full h-16 rounded-lg mb-2"
                style={{ backgroundColor: "var(--color-success-600)" }}
              ></div>
              <p className="caption">Success</p>
            </div>
            <div className="text-center">
              <div
                className="w-full h-16 rounded-lg mb-2"
                style={{ backgroundColor: "var(--color-warning-600)" }}
              ></div>
              <p className="caption">Warning</p>
            </div>
            <div className="text-center">
              <div
                className="w-full h-16 rounded-lg mb-2"
                style={{ backgroundColor: "var(--color-error-600)" }}
              ></div>
              <p className="caption">Error</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Layout Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Layout Grid</CardTitle>
          <CardDescription>
            Responsive grid system with consistent spacing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-primary-light p-4 rounded-lg">
              <h6 className="heading-6 mb-2">Grid Item 1</h6>
              <p className="body-small">Responsive grid item</p>
            </div>
            <div className="bg-success-light p-4 rounded-lg">
              <h6 className="heading-6 mb-2">Grid Item 2</h6>
              <p className="body-small">Responsive grid item</p>
            </div>
            <div className="bg-warning-light p-4 rounded-lg">
              <h6 className="heading-6 mb-2">Grid Item 3</h6>
              <p className="body-small">Responsive grid item</p>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button variant="outline" className="mr-2">
            Cancel
          </Button>
          <Button variant="primary">Save Changes</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
